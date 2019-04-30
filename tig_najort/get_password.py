#!/usr/bin/env python3
import getpass
import re

message = 'Please enter the password: '


def get_a_password(message=message):
    '''
    Request password from user that is at least 8 chars long
    with characters that are lowercase, uppercase, and numbers
    '''
    try:
        min_pass_length = 8
        password = ''
        attempts = 3
        while (
                password == '' and
                len(password) < min_pass_length and
                attempts > 0):

            password = getpass.getpass(message)
            password_check = [len(password) >= min_pass_length]
            password_check.append(re.search(r'[a-z]', password))
            password_check.append(re.search(r'[A-Z]', password))
            password_check.append(re.search(r'[0-9]', password))

            if not all(password_check):
                print(
                    'Password too weak: minimum 8 letters, '
                    'different case and numbers')
                password = ''
                attempts -= 1
            if attempts == 0:
                raise ValueError('Encountered problem getting a password.')
    except ValueError as gve:
        print('Too many attempts.')
        exit(0)
    except Exception:
        raise

    return password
