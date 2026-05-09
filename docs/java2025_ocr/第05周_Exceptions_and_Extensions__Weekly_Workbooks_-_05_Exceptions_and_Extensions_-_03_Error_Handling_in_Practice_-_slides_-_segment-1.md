# Exceptions From Scratch

- Java has a whole host of exceptions built in
  - IOException
  - ArrayIndexOutOfBoundsException
  - NullPointerException
- These are mostly generated behind the scenes, for example when you try to open a file or accidentally overwrite an array, and all you need to do is handle (or “catch”) them
- But sometimes you want specialised exceptions

---

# Special Exception

```java
public class InvalidPasswordException extends Exception{
    private final String failMessage;

    public InvalidPasswordException(String message) {
        failMessage = message;
    }

    public String toString() {
        return this.getClass().getName() + ": " + failMessage;
    }
}

---

public class Register {
    private final String username;
    private final String password;

    public Register(String username, String password) {
        this.username = username;
        this.password = password;
        try {
            validatePassword();
            createAccount();
        } catch (InvalidPasswordException ipe) {
            System.out.println("Registration Failed. " + ipe.toString());
        }
    }

    private void validatePassword() throws InvalidPasswordException {
        if (password.length() < 8) {
            throw new InvalidPasswordException("Password must be at least 8 characters long.");
        } else if (!password.contains("[0-9]+")) {
            throw new InvalidPasswordException("Password must contain at least one number.");
        }
    }

    private void createAccount() {}
}

---

public class Register {
    private final String username;
    private final String password;

    public Register(String username, String password) throws InvalidPasswordException {
        this.username = username;
        this.password = password;
        validatePassword();
        createAccount();
    }

    private void validatePassword() throws InvalidPasswordException {
        if (password.length() < 8) {
            throw new InvalidPasswordException("Password must be at least 8 characters long.");
        } else if (!password.contains("[0-9]+")) {
            throw new InvalidPasswordException("Password must contain at least one number.");
        }
    }

    private void createAccount() {}
}