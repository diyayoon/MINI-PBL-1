import hashlib
import io

from PIL import Image


MAGIC = b"PAB1"


def _keystream(key: str, length: int) -> bytes:
    key_bytes = key.encode("utf-8")
    output = bytearray()
    counter = 0

    while len(output) < length:
        hash_block = hashlib.sha256(
            key_bytes + counter.to_bytes(8, "big")
        ).digest()

        output.extend(hash_block)
        counter += 1

    return bytes(output[:length])


def _xor(data: bytes, key: str) -> bytes:
    keystream = _keystream(key, len(data))

    return bytes(
        value ^ stream
        for value, stream in zip(data, keystream)
    )


def _img_to_channels(image: Image.Image):
    if image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size
    pixels = list(image.getdata())

    channels = []

    for red, green, blue in pixels:
        channels.extend((red, green, blue))

    return image, width, height, channels


def _channels_to_img(width: int, height: int, channels):
    iterator = iter(channels)
    pixels = list(zip(iterator, iterator, iterator))

    image = Image.new("RGB", (width, height))
    image.putdata(pixels)

    return image


def _bytes_to_2bit_chunks(data: bytes):
    for byte in data:
        yield (byte >> 6) & 0b11
        yield (byte >> 4) & 0b11
        yield (byte >> 2) & 0b11
        yield byte & 0b11


def _chunks2_to_bytes(chunks):
    output = bytearray()
    iterator = iter(chunks)

    for a, b, c, d in zip(iterator, iterator, iterator, iterator):
        byte = (
            ((a & 0b11) << 6)
            | ((b & 0b11) << 4)
            | ((c & 0b11) << 2)
            | (d & 0b11)
        )

        output.append(byte)

    return bytes(output)


def _build_payload(
    original_bytes: bytes,
    original_ext: str,
    key: str
) -> bytes:
    ext_clean = (original_ext or "").lower().lstrip(".")[:8]
    ext_length = len(ext_clean)
    original_size = len(original_bytes)

    cipher = _xor(original_bytes, key)

    header = (
        MAGIC
        + bytes([ext_length])
        + ext_clean.encode("ascii", "ignore")
        + original_size.to_bytes(4, "big")
    )

    return header + cipher


def embed_lsb_2bit(
    cover_path: str,
    original_bytes: bytes,
    original_ext: str,
    key: str
) -> bytes:
    image = Image.open(cover_path)
    image, width, height, channels = _img_to_channels(image)

    payload = _build_payload(original_bytes, original_ext, key)

    needed_bits = len(payload) * 8
    capacity_bits = width * height * 3 * 2

    if needed_bits > capacity_bits:
        raise ValueError(
            f"Payload terlalu besar ({len(payload)} bytes) "
            f"untuk cover ini. Maks ~{capacity_bits // 8} bytes. "
            "Gunakan cover yang lebih besar atau file asli yang lebih kecil."
        )

    chunks = _bytes_to_2bit_chunks(payload)
    modified_channels = list(channels)

    index = 0

    for two_bits in chunks:
        modified_channels[index] = (
            (modified_channels[index] & 0b11111100)
            | (two_bits & 0b11)
        )

        index += 1

    output_image = _channels_to_img(
        width,
        height,
        modified_channels
    )

    buffer = io.BytesIO()
    output_image.save(buffer, format="PNG")

    return buffer.getvalue()


def extract_lsb_2bit(stego_path: str, key: str):
    image = Image.open(stego_path)
    image, width, height, channels = _img_to_channels(image)

    required_first_bytes = 5
    chunks = []

    for value in channels:
        chunks.append(value & 0b11)

        if len(chunks) >= required_first_bytes * 4:
            break

    header_first = _chunks2_to_bytes(chunks)

    if header_first[:4] != MAGIC:
        raise ValueError(
            "Stego tidak mengandung payload PeekABoo "
            "atau kunci salah."
        )

    ext_length = header_first[4]
    header_size = 4 + 1 + ext_length + 4

    while len(chunks) < header_size * 4:
        index = len(chunks)

        if index >= len(channels):
            raise ValueError("Data tidak lengkap.")

        chunks.append(channels[index] & 0b11)

    header = _chunks2_to_bytes(chunks)[:header_size]

    position = 5

    extension = header[position:position + ext_length].decode(
        "ascii",
        "ignore"
    )
    position += ext_length

    original_size = int.from_bytes(
        header[position:position + 4],
        "big"
    )

    required_chunks = (header_size + original_size) * 4

    while len(chunks) < required_chunks:
        index = len(chunks)

        if index >= len(channels):
            raise ValueError(
                "Data tidak lengkap (cipher terpotong)."
            )

        chunks.append(channels[index] & 0b11)

    full_payload = _chunks2_to_bytes(chunks)[
        :header_size + original_size
    ]

    cipher = full_payload[
        header_size:header_size + original_size
    ]

    original_bytes = _xor(cipher, key)

    return original_bytes, extension
