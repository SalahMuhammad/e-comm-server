import string
import random

# Algorithm 1: Base62 Encoding with Padding
class Base62Encoder:
    def __init__(self):
        # Use alphanumeric characters (0-9, A-Z, a-z) = 62 characters
        self.charset = string.digits + string.ascii_uppercase + string.ascii_lowercase
        self.base = len(self.charset)
    
    def encode(self, number):
        """Encode a number to exactly 8 characters using base62"""
        if number < 0:
            raise ValueError("Only non-negative numbers are supported")
        
        if number == 0:
            return "00000000"
        
        # Convert to base62
        result = ""
        while number > 0:
            result = self.charset[number % self.base] + result
            number //= self.base
        
        # Pad with zeros to make exactly 8 characters
        return result.zfill(8)
    
    def decode(self, encoded):
        """Decode an 8-character string back to a number"""
        if len(encoded) != 8:
            raise ValueError("Encoded string must be exactly 8 characters")
        
        number = 0
        for char in encoded:
            if char not in self.charset:
                raise ValueError(f"Invalid character: {char}")
            number = number * self.base + self.charset.index(char)
        
        return number


# Algorithm 2: Custom Mixed Radix with Checksum
class MixedRadixEncoder:
    def __init__(self):
        # Use different character sets for different positions
        self.charsets = [
            string.digits,                    # Position 0: 0-9 (10 chars)
            string.ascii_uppercase,           # Position 1: A-Z (26 chars)  
            string.ascii_lowercase,           # Position 2: a-z (26 chars)
            string.digits + string.ascii_uppercase[:6],  # Position 3: 0-9A-F (16 chars)
            string.ascii_lowercase[:20],      # Position 4: a-t (20 chars)
            string.digits + string.ascii_uppercase[:12], # Position 5: 0-9A-L (22 chars)
            string.ascii_lowercase[10:20],    # Position 6: k-t (10 chars)
            string.digits + string.ascii_uppercase[:6]   # Position 7: 0-9A-F (16 chars) - checksum
        ]
#         self.charsets = [
#     string.digits + string.ascii_uppercase,          # Position 0: 0-9A-Z (36 chars)
#     string.digits + string.ascii_lowercase,          # Position 1: 0-9a-z (36 chars)
#     string.ascii_uppercase + string.ascii_lowercase, # Position 2: A-Za-z (52 chars)
#     string.digits + string.ascii_letters,           # Position 3: 0-9A-Za-z (62 chars)
#     string.digits + string.ascii_letters,           # Position 4: 0-9A-Za-z (62 chars)
#     string.digits + string.ascii_letters,           # Position 5: 0-9A-Za-z (62 chars)
#     string.digits + string.ascii_letters,           # Position 6: 0-9A-Za-z (62 chars)
#     string.digits + string.ascii_uppercase[:6]      # Position 7: 0-9A-F (checksum)
# ]
        self.radixes = [len(charset) for charset in self.charsets[:-1]]  # Exclude checksum position
    
    def encode(self, number):
        """Encode a number using mixed radix system with checksum"""

        if number < 0:
            raise ValueError("Only non-negative numbers are supported")
        
        # Calculate maximum encodable number
        max_num = 1
        for radix in self.radixes:
            max_num *= radix
        max_num -= 1
        
        if number > max_num:
            raise ValueError(f"Number too large. Maximum encodable: {max_num}")
        
        # Convert to mixed radix representation
        digits = []
        temp = number
        
        for radix in reversed(self.radixes):
            digits.append(temp % radix)
            temp //= radix
        
        digits.reverse()
        
        # Convert digits to characters
        result = ""
        checksum = 0
        for i, digit in enumerate(digits):
            char = self.charsets[i][digit]
            result += char
            checksum += digit
        
        # Add checksum character
        checksum_char = self.charsets[7][checksum % len(self.charsets[7])]
        result += checksum_char
        
        return result
    
    def decode(self, encoded):
        """Decode an 8-character string back to a number with checksum validation"""
        if len(encoded) != 8:
            raise ValueError("Encoded string must be exactly 8 characters")
        
        # Extract digits and validate characters
        digits = []
        checksum = 0
        
        for i in range(7):  # First 7 positions
            char = encoded[i]
            if char not in self.charsets[i]:
                raise ValueError(f"Invalid character '{char}' at position {i}")
            
            digit = self.charsets[i].index(char)
            digits.append(digit)
            checksum += digit
        
        # Validate checksum
        expected_checksum_char = self.charsets[7][checksum % len(self.charsets[7])]
        if encoded[7] != expected_checksum_char:
            raise ValueError("Checksum validation failed")
        
        # Convert back to number
        number = 0
        for i, digit in enumerate(digits):
            for j in range(i + 1, len(self.radixes)):
                digit *= self.radixes[j]
            number += digit
        
        return number


class EnhancedMixedRadixEncoder(MixedRadixEncoder):
    def __init__(self):
        super().__init__()
        self.avalanche_helper = AvalancheHelper()
        # Add additional charset for salt
        self.salt_charset = string.ascii_letters + string.digits
    
    def encode(self, number):
        """Encode a number using mixed radix system with avalanche effect"""
        if number < 0:
            raise ValueError("Only non-negative numbers are supported")
            
        # Create avalanche effect
        avalanche_num, salt = self.avalanche_helper.create_avalanche(number)
        
        # XOR the original number with avalanche number
        enhanced_number = number ^ (avalanche_num & 0xFFFFFFFF)
        
        # Encode using mixed radix
        encoded = super().encode(enhanced_number)
        
        # Return encoded string with salt
        return encoded + salt
    
    def decode(self, encoded):
        """Decode with avalanche validation"""
        if len(encoded) != 12:  # 8 chars for encoding + 4 chars salt
            raise ValueError("Encoded string must be 12 characters")
            
        # Split encoded string and salt
        main_encoded = encoded[:8]
        salt = encoded[8:]
        
        # Decode the enhanced number
        enhanced_number = super().decode(main_encoded)
        
        # Recreate avalanche effect
        avalanche_num, _ = self.avalanche_helper.create_avalanche(enhanced_number, salt_length=4)
        
        # Reverse the XOR operation
        original_number = enhanced_number ^ (avalanche_num & 0xFFFFFFFF)
        
        # Verify the result
        verify_avalanche, _ = self.avalanche_helper.create_avalanche(original_number, salt_length=4)
        if (verify_avalanche & 0xFFFFFFFF) ^ original_number != enhanced_number:
            raise ValueError("Avalanche validation failed - data may be corrupted")
            
        return original_number


class EnhancedBase62Encoder(Base62Encoder):
    def __init__(self):
        super().__init__()
        self.avalanche_helper = AvalancheHelper()
    
    def encode(self, number):
        """Encode a number with avalanche effect"""
        if number < 0:
            raise ValueError("Only non-negative numbers are supported")
        
        # Create avalanche effect
        avalanche_num, salt = self.avalanche_helper.create_avalanche(number)
        
        # Combine original number with avalanche effect
        combined = (number << 32) | avalanche_num
        
        # Encode using base62
        encoded = super().encode(combined)
        
        # Return encoded string with salt
        return encoded + salt
    
    def decode(self, encoded):
        """Decode a string with avalanche validation"""
        if len(encoded) != 12:  # 8 chars for encoding + 4 chars salt
            raise ValueError("Encoded string must be 12 characters")
            
        # Split encoded string and salt
        main_encoded = encoded[:8]
        salt = encoded[8:]
        
        # Decode the combined number
        combined = super().decode(main_encoded)
        
        # Extract original number and avalanche number
        original_number = combined >> 32
        avalanche_num = combined & 0xFFFFFFFF
        
        # Verify avalanche effect
        new_avalanche, _ = self.avalanche_helper.create_avalanche(original_number, salt_length=4)
        if (new_avalanche & 0xFFFFFFFF) != avalanche_num:
            raise ValueError("Avalanche validation failed - data may be corrupted")
            
        return original_number


# Demo and testing
if __name__ == "__main__":
    # Test Algorithm 1: Base62
    print("=== Algorithm 1: Base62 Encoding ===")
    base62 = Base62Encoder()
    
    test_numbers = [0, 1, 42, 1337, 123456, 999999999]
    
    for num in test_numbers:
        try:
            encoded = base62.encode(num)
            decoded = base62.decode(encoded)
            print(f"{num:>10} -> {encoded} -> {decoded:>10} {'✓' if num == decoded else '✗'}")
        except ValueError as e:
            print(f"{num:>10} -> Error: {e}")
    
    print(f"\nMax encodable (Base62): {62**8 - 1:,}")
    
    # Test Algorithm 2: Mixed Radix
    print("\n=== Algorithm 2: Mixed Radix with Checksum ===")
    mixed = MixedRadixEncoder()
    
    for num in test_numbers:
        try:
            encoded = mixed.encode(num)
            decoded = mixed.decode(encoded)
            print(f"{num:>10} -> {encoded} -> {decoded:>10} {'✓' if num == decoded else '✗'}")
        except ValueError as e:
            print(f"{num:>10} -> Error: {e}")
    
    # Calculate max for mixed radix
    max_mixed = 1
    for radix in mixed.radixes:
        max_mixed *= radix
    max_mixed -= 1
    print(f"\nMax encodable (Mixed Radix): {max_mixed:,}")
    
    # Test error detection in mixed radix
    print("\n=== Error Detection Test ===")
    original = mixed.encode(12345)
    print(f"Original: {original}")
    
    # Corrupt one character
    corrupted = original[:3] + 'X' + original[4:]
    try:
        mixed.decode(corrupted)
        print("Error detection failed!")
    except ValueError as e:
        print(f"Error detected: {e}")


import random
import hashlib

class AvalancheHelper:
    @staticmethod
    def create_avalanche(number, salt_length=4):
        """Creates an avalanche effect by combining the number with a random salt"""
        # Convert number to bytes
        number_bytes = str(number).encode('utf-8')
        # Create random salt
        salt = ''.join(random.choices(string.ascii_letters + string.digits, k=salt_length))
        salt_bytes = salt.encode('utf-8')
        
        # Combine number and salt, then hash
        combined = number_bytes + salt_bytes
        hashed = hashlib.sha256(combined).digest()
        
        # Use first 4 bytes of hash as integer
        avalanche_num = int.from_bytes(hashed[:4], byteorder='big')
        return avalanche_num, salt

    @staticmethod
    def reverse_avalanche(encoded_num, salt):
        """Validates the avalanche effect using the salt"""
        # Will be implemented based on specific encoder needs
        pass
