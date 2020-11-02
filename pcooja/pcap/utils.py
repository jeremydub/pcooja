def human_readable_address(address_bytes, bytes_per_group=2):
  address=""
  size=len(address_bytes)
  for i in range(size):
    if i % bytes_per_group==0 and i > 0:
      address += ":"
    address += hex(address_bytes[i])[2:].zfill(2)
  return address

def address_from_str(string, length=16):
  if type(string) == str:
    blocks = string.split(":")
    address = []

    for block in blocks:
      if len(block) != 0:
        block = block.rjust(4,"0")
        if length == 16:
          address.append(int(block[:2], 16))
        address.append(int(block[2:], 16))
      elif length == 16:
        for i in range(8-len(blocks)+1):
          address.append(0)
          address.append(0)
    return address

  else :
    return []