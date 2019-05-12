#!/usr/bin/env python3
'''
Note on Apr-2019:
This module is only meant to provide a way to encrypt small files
in a limited manner. Keep the custom.salt file and
password in a safe place, files encrypted using AES-128.
'''
import base64
import argparse
import sys
from os import path, urandom
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Custom Modules
import get_password
message = 'Please enter the password: '


def derive_key(password, salt_file_path='custom.salt', test=False):
    '''
    Takes the password provided along with contents of custom.salt to derive
    the encryption key. When test is True, the default salt is accepted without
    question
    '''
    default_salt = b'asdf_static_salt!'
    salt = ''
    # Check for valid password type
    if isinstance(password, (bytes, str)):
        if isinstance(password, str):
            password = password.encode()
    else:
        raise TypeError('Password should be bytes or string.')

    try:
        if not Path(salt_file_path).exists():
            raise ValueError(
                'Salt file path not found: '
                '{}'.format(salt_file_path))
        else:
            with open(salt_file_path, 'rb') as salt_file:
                salt_lines = b''.join(salt_file.readlines())
                if isinstance(salt_lines, str):
                    salt = salt_lines.strip().encode()
                else:
                    salt = salt_lines
    except Exception:
        raise

    try:
        if test:
            salt = default_salt
        # Else check if default salt is being used and whether user can
        # interact or not
        elif salt == default_salt and sys.__stdout__.isatty():
            gen_salt = input('Would you like to randomize the salt?: [Y/n] ')
            if not gen_salt.lower() == 'n':
                salt = urandom(16)
                with open('custom.salt', 'wb') as salt_file:
                    salt_file.write(salt)
                print('New salt: {}'.format(salt))
            else:
                raise Warning('Using default salt value; update "custom.salt"')
    except Warning as wdk:
        print('Warning: {}'.format(wdk))
        pass
    except Exception:
        raise
    # Meant only to make rainbow tables useless in case a weak password
    # is chosen.
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend())
    del salt

    return base64.urlsafe_b64encode(kdf.derive(password))


def encrypt_file(file_name, password, overwrite=False, test=False):
    '''
    Encrypts the file indicated by the provided parameter and saves it with
    a new ".enc" extension.

    Returns the key used to encrypt the file.
    '''
    fernet_key = derive_key(password, test=test)
    cipher_suite = Fernet(fernet_key)
    try:
        # Some quick file checks, size and path verification
        if not isinstance(file_name, str):
            raise TypeError('File name should be a string.')
        # Files that are "too large" will have problems since the Fernet
        # library does all the encryption in memory. It's fast though.
        if path.getsize(file_name) > 1024000:
            raise Warning('File is quite large.')

        if Path(file_name + '.enc').exists() and not overwrite:
            raise ValueError('Target file {}.enc already exists'.format(
                file_name))

        cipher_text = None

        with open(file_name, 'r') as plain_file:
            cipher_text = cipher_suite.encrypt(
                ''.join(plain_file.readlines()).strip().encode())
        if cipher_text:
            with open(file_name + '.enc', 'wb') as cipher_file:
                cipher_file.write(cipher_text)
            print('File saved as: {}'.format(file_name + '.enc'))
        else:
            raise ValueError('Unable to write cipher text to file.')
    except Warning:
        pass
    except Exception as ecf:
        raise

    return fernet_key


def decrypt_file(file_name, password, test=False):
    '''
    Decrypts the file indicated by the provided parameter.
    Returns the decrypted file contents. No changes will be made to files,
    only the content of the file will be returned.
    '''
    fernet_key = derive_key(password, test=test)
    cipher_suite = Fernet(fernet_key)
    plain_text = ''
    try:
        with open(file_name, 'rb') as cipher_file:
            for line in cipher_file:
                plain_text += bytes(cipher_suite.decrypt(line)).decode('utf-8')

        return plain_text
    except FileNotFoundError as fne:
        print('Credentials file not found')
    except InvalidToken as it:
        print('Password or custom salt was incorrect.')
    except Exception:
        raise


def write_custom_salt(salt=b'asdf_static_salt!', salt_file_path='custom.salt'):
    if not Path(salt_file_path).exists():
        if isinstance(salt, str):
            custom_salt = salt.encode()
        if isinstance(custom_salt, bytes):
            with open(salt_file_path, 'wb') as salt_file:
                salt_file.write(custom_salt)
        else:
            raise TypeError('Salt provided needs to be a string or bytes')
    else:
        print('Custom salt file exists. Please rename or remove the old file.')


def get_file_credentials(file_name, password=None, confirm=False):
    input_file = input(
        'Which file containes the encrypted credentials?'
        ' [{}]: '.format(file_name))

    # Nothing entered:
    if len(input_file) < 1 and Path(file_name).exists():
        context_file = file_name

    # Check for too long input, and whether files exists or not
    elif (
            len(input_file) > 254 or
            (not Path(input_file).exists() and not Path(file_name).exists())):
        raise ValueError('File path entered is not valid')

    # File indicated exist afterall, make it our context target
    else:
        context_file = input_file

    if password is None:
        password = get_password.get_a_password(message=message)

    if isinstance(password, str) and len(password) >= 8:
        # Looks legit, decrypt the file
        return decrypt_file(context_file, password)
    else:
        raise TypeError('Password should be a string!')


if __name__ == '__main__':
    a_parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            '''
File Encryption Tool. Allows in-memory encryption/decryption of files. Use only
for small files(less than a few MB).

Notes:
** Please test decryption before deleting the orginal file.
This module is only meant to provide a way to encrypt small files
in an efficient manner. Keep the custom.salt file protected and
remember or save the password in a safe place.

Files encrypted using AES-128.

Examples:
NEW SALT: python3 encrypt.py -s '<custom salt contents>'
ENCRYPTION: python3 encrypt.py -f <file_name> -e
DECYPTION: python3 encrypt.py -f <file_name> -d
            '''))
    a_parser.add_argument(
        '-s',
        '--salt',
        help=(
            'Save new custom salt file'))
    a_parser.add_argument(
        '-f',
        '--file',
        help='Path of file to encrypt/decrypt')
    a_parser.add_argument(
        '-p',
        '--password',
        help='Password used to encrypt or decrypt the file.')
    en_or_ed = a_parser.add_mutually_exclusive_group()
    en_or_ed.add_argument(
        '-e',
        '--encrypt',
        action='store_true',
        help=(
            'Encrypt a file'))
    en_or_ed.add_argument(
        '-d',
        '--decrypt',
        action='store_true',
        help=(
            'Decrypt a file'))

    action_args = a_parser.parse_args()

    if (not action_args.salt and
            (not action_args.file or not Path(action_args.file).exists())):
        raise ValueError('Invalid argument options provided')

    if action_args.salt:
        salt = write_custom_salt(action_args.salt)
        if salt:
            exit(0)
        else:
            raise RuntimeError(
                'Problem while trying to write to '
                'the custom salt file')

    try:
        password = ''
        if (  # Check if provided password is string type
                not action_args.password or
                not isinstance(action_args.password, str)):
            password = get_password.get_a_password(
                message='Enter the password: ')
        else:
            password = action_args.password
    except Exception:
        print('I had a bad day getting a password')
        del password
        del action_args.password
        raise

    try:
        # Act on file selected
        if action_args.file:
            # Decryption action selected
            if action_args.decrypt:
                print(decrypt_file(action_args.file, password))

            # Encryption action selected
            elif action_args.encrypt:
                # Check if encrypted file exists already
                if Path(action_args.file + '.enc').exists():
                    raise ValueError(
                        'Target file {}.enc already exists'.format(
                            action_args.file))

                # Confirm the password
                tries = 3
                password2 = None
                while ((password is None or password != password2) and
                        tries > 0):
                    if password is None:
                        password = get_password.get_a_password(message=(
                            'Enter the password: '))

                    password2 = get_password.get_a_password(
                        message=('Please confirm the password: '))
                    if password != password2:
                        print('\n--Passwords do not match--\n')
                        password = None
                    tries -= 1
                if tries == 0:
                    raise ValueError('Too many attempts')
                del password2

                encrypt_file(action_args.file, password)

            # No action selected
            else:
                raise ValueError('Please indicate encrypt or decrypt action.')

    except Exception as ep:
        print(
            'Something went wrong. Likely a bad password or bad file.\n{}'
            ''.format(ep))
        raise
    finally:
        del password
        del password2
