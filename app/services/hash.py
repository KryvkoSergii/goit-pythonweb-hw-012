from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify whether a plain password matches a hashed password.

    This function compares a plaintext password with a hashed password 
    using the `bcrypt` hashing algorithm.

    :param plain_password: The plaintext password to be verified.
    :type plain_password: str

    :param hashed_password: The hashed password stored in the database.
    :type hashed_password: str

    :return: `True` if the passwords match, otherwise `False`.
    :rtype: bool

    :example:
        >>> is_valid = verify_password("my_secure_password", hashed_password)
        >>> print(is_valid)  # Output: True or False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate a secure hash for a given password.

    This function hashes the given password using the `bcrypt` hashing algorithm.

    :param password: The plaintext password to be hashed.
    :type password: str

    :return: A hashed version of the password.
    :rtype: str

    :example:
        >>> hashed_password = get_password_hash("my_secure_password")
        >>> print(hashed_password)
    """
    return pwd_context.hash(password)
