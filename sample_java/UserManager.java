
package com.example.app;

import java.util.List;
import java.util.ArrayList;
import java.util.HashMap;

/**
 * UserManager class handles user operations
 */
public class UserManager {

    private List<User> users;
    private HashMap<String, User> userMap;

    /**
     * Constructor initializes the user collections
     */
    public UserManager() {
        this.users = new ArrayList<>();
        this.userMap = new HashMap<>();
    }

    /**
     * Adds a new user to the system
     * @param user The user to add
     * @return true if successful, false otherwise
     */
    public boolean addUser(User user) {
        if (user == null || user.getId() == null) {
            return false;
        }

        if (userMap.containsKey(user.getId())) {
            return false; // User already exists
        }

        users.add(user);
        userMap.put(user.getId(), user);
        return true;
    }

    /**
     * Retrieves a user by their ID
     * @param userId The user's ID
     * @return The user if found, null otherwise
     */
    public User getUser(String userId) {
        return userMap.get(userId);
    }

    /**
     * Removes a user from the system
     * @param userId The ID of the user to remove
     * @return true if removed, false if not found
     */
    public boolean removeUser(String userId) {
        User user = userMap.remove(userId);
        if (user != null) {
            users.remove(user);
            return true;
        }
        return false;
    }

    /**
     * Gets all users in the system
     * @return List of all users
     */
    public List<User> getAllUsers() {
        return new ArrayList<>(users);
    }
}
