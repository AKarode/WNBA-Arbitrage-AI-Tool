package model;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Represents a central system for scheduling events. It provides functionalities to manage users
 * and their events, including adding, removing, and updating users and events within the system.
 */
public class CentralSystem implements PlannerModel {

  private List<User> users;


  public CentralSystem() {
    this.users = new ArrayList<>();
  }

  @Override
  public void addUser(User u) {
    if (u != null) {
      for (int i = 0; i < this.users.size(); i++) {
        if (this.users.get(i).getName().equals((u.getName()))) {
          return;
        }
      }

      this.users.add(u);

      List<Event> events = u.getSchedule().getEvents();

    }
  }

  @Override
  public void removeUser(User u) {
    if (u == null) {
      throw new IllegalArgumentException();
    }

    for (int i = 0; i < this.users.size(); i++) {
      if (this.users.get(i).getName().equals((u.getName()))) {
        this.users.remove(i);
      }
    }
  }

  @Override
  public User getUser(String name) {
    if (name == null) {
      throw new IllegalArgumentException("Not a valid input");
    }
    for (int i = 0; i < this.users.size(); i++) {
      if (this.users.get(i).getName().equals((name))) {
        return new User(this.users.get(i));
      }
    }
    throw new IllegalArgumentException("The user could not be founud");
  }

  @Override
  public List<User> getUsers() {
    return this.users;
  }

  @Override
  public void createEvent(Event event) {
    // First, check if the host is part of the central system and add the event to their schedule
    User host = getUser(event.getHost().getName());
    if (host != null) {
      if (host.getSchedule() == null) {
        host.setSchedule(new Schedule(host));
      }
      host.getSchedule().addEvent(event); // Add the event to the host's schedule
    } else {
      throw new IllegalArgumentException("Host does not exist in the central system");
    }

    // Next, iterate over the list of invited users and add the event to their schedules
    for (User invitedUser : event.getInvitedUsers()) {
      User centralSystemUser = getUser(invitedUser.getName());
      if (centralSystemUser != null) {
        if (centralSystemUser.getSchedule() == null) {
          centralSystemUser.setSchedule(new Schedule(centralSystemUser));
        }
        centralSystemUser.getSchedule().addEvent(event); // Add the event to the user's schedule
      } else {
        // Optionally handle the case where an invited user does not exist in the central system
        // For example, you might choose to add them to the system here
        // Or you might throw an exception or log a warning
      }
    }
  }


  /**
   * Modifies an existing event by updating its name.
   *
   * @param eventName the current name of the event to be modified
   * @param newName the new name to assign to the event
   */
  public void changeEventName(String eventName, String newName) {
    for (User user : users) {
      for (Event event : user.getSchedule().getEvents()) {
        if (event.getName().equals(eventName)) {
          event.setName(newName);
        }
      }
    }
  }

  /**
   * Updates the location and online status of an existing event.
   *
   * @param eventName   the name of the event to update
   * @param newLocation the new location of the event; if the event is online,
   *                    this can be a URL or a descriptive location
   * @param isOnline    a boolean flag indicating whether the event
   *                    is online (true) or in-person (false)
   */
  public void changeEventLocation(String eventName, String newLocation, boolean isOnline) {
    for (User user : users) {
      for (Event event : user.getSchedule().getEvents()) {
        if (event.getName().equals(eventName)) {
          event.setLocation(newLocation);
          event.setOnlineStatus(isOnline);
        }
      }
    }
  }

  /**
   * Updates the timing for a specified event.
   * This method changes the start and end dates and times for an existing event.
   * It returns true if the update is successful,
   * indicating that the event exists and the new timing is valid.
   * It returns false if the event does not exist or the new timing is not valid
   * (e.g., start time is after end time).
   *
   * @param eventName the name of the event to update
   * @param newStartDay the new start date of the event in a specific format (e.g., YYYY-MM-DD)
   * @param newStartTime the new start time of the event (e.g., HH:MM in 24-hour format)
   * @param newEndDay the new end date of the event in the same format as the start date
   * @param newEndTime the new end time of the event in the same format as the start time
   * @return boolean true if the event timing is successfully updated, false otherwise
   */
  public boolean changeEventTiming(String eventName, String newStartDay, String newStartTime,
                                   String newEndDay, String newEndTime) {
    Event tempEvent = new Event(eventName, null, false, newStartDay,
        newStartTime, newEndDay, newEndTime, null, null);
    for (User user : users) {
      for (Event event : user.getSchedule().getEvents()) {
        if (event.getName().equals(eventName)) {
          if (event.getHost().getSchedule().getEvents().stream()
              .anyMatch(e -> !e.getName().equals(eventName)
              && e.isOverLapping(tempEvent))) {
            System.out.println("New event timing overlaps with an existing event for the host.");
            return false;
          }
          for (User invitedUser : event.getInvitedUsers()) {
            if (invitedUser.getSchedule().getEvents().stream()
                .anyMatch(e -> !e.getName().equals(eventName)
                && e.isOverLapping(tempEvent))) {
              System.out.println("New event timing overlaps with an existing event for an invited"
                  + " user: " + invitedUser.getName());
              return false;
            }
          }
          event.setStartDay(newStartDay);
          event.setStartTime(newStartTime);
          event.setEndDay(newEndDay);
          event.setEndDay(newEndDay); 
          return true;
        }
      }
    }
    return true;
  }


  /**
   * Updates the host of a specified event.
   * This method assigns a new host to an existing event.
   * It is designed to handle cases where events
   * need to be managed or reassigned to different hosts.
   * The success of the operation might depend on the implementation details,
   * such as whether the event and the new host exist within the system.
   *
   * @param eventName the name of the event for which the host is to be changed
   * @param newHost the name or identifier of the new host taking over the event
   */
  public boolean changeEventHost(String eventName, User newHost) {
    boolean eventFound = false;
    for (User user : users) {
      List<Event> userEvents = user.getSchedule().getEvents();
      for (int i = 0; i < userEvents.size(); i++) {
        Event event = userEvents.get(i);
        if (Objects.equals(event.getName(), eventName)) {
          // If the event is found in a user's schedule who is not the current host, continue.
          if (!Objects.equals(event.getHost().getName(), user.getName())) {
            continue;
          }
          // Remove the event from the old host's schedule.
          userEvents.remove(event);

          // Add the event to the new host's schedule.
          newHost.getSchedule().addEvent(event);

          // Update the event's host.
          event.setHost(newHost);

          // Add the event back to all invited users' schedules, including the new host
          for (User invitedUser : event.getInvitedUsers()) {
            if (!Objects.equals(invitedUser.getName(), newHost.getName())) {
              invitedUser.getSchedule().addEvent(event);
            }
          }

          eventFound = true;
          // Assuming each event name is unique per host, break after successful operation.
          break;
        }
      }
      // Early exit if the event host has been changed
      if (eventFound) {
        break;
      }
    }
    return eventFound;
  }

  /**
   * Change the list of invited users for an event.
   *
   * @param eventName       the name of the event
   * @param newInvitedUsers the new list of invited users
   */
  public void changeEventInvitedUsers(String eventName, List<User> newInvitedUsers) {
    for (User user : users) {
      for (Event event : user.getSchedule().getEvents()) {
        if (event.getName().equals(eventName)) {
          event.setInvitedUsers(newInvitedUsers);
        }
      }
    }
  }

  /**
   * Updates an existing event in the system.
   * This involves removing the original event from the host's
   * and all invited users' schedules and adding the updated event in its place.
   * This method assumes that the updated event has the
   * same host and invited users as the original event.
   * If the host or list of invited users needs to be changed,
   * other methods should be used in conjunction
   * with this one to ensure data integrity across the system.
   *
   * @param originalEvent The original event to be updated.
   *                      This event will be removed from all relevant schedules.
   * @param updatedEvent The new event that will replace the original event in all schedules.
   */
  public void updateEvent(Event originalEvent, Event updatedEvent) {

    // Update the event in the host's schedule
    User host = originalEvent.getHost();
    if (host != null && host.getSchedule() != null) {
      host.getSchedule().getEvents().remove(originalEvent);
      host.getSchedule().getEvents().add(updatedEvent);
    }

    // Update the event in all invited users' schedules, if they differ from the host
    for (User invitedUser : originalEvent.getInvitedUsers()) {
      // Check if the invited user is not the host to avoid duplicate operations
      if (!invitedUser.equals(host)) {
        invitedUser.getSchedule().getEvents().remove(originalEvent);
        invitedUser.getSchedule().getEvents().add(updatedEvent);
      }
    }
  }

  /**
   * Remove an event from all users' schedules.
   *
   * @param eventToRemove the event to be removed
   */
  public void removeEvent(Event eventToRemove) {
    for (User user : users) {
      user.getSchedule().removeEvent(eventToRemove);
    }
  }

  /**
   * Adds a user to the central system from an XML file.
   * If the user already exists, a message is printed instead of adding the user.
   *
   * @param filePath the path to the XML file containing the user's information
   */
  public void addUserFromXML(String filePath) {
    XMLReader reader = new XMLReader();
    User user = reader.readXML(filePath);

    boolean userExists = users.stream().anyMatch(u -> u.getName().equals(user.getName()));
    if (!userExists) {
      users.add(user);
    } else {
      System.out.println("User already exists in the system.");
    }
  }

  /**
   * Exports a user's schedule to an XML file.
   * If the user does not exist, prints a message instead.
   *
   * @param userName the name of the user whose schedule is to be exported
   * @param filePath the path to the XML file where the schedule should be saved
   */
  public void exportUserScheduleToXML(String userName, String filePath) {
    User user = getUser(userName);
    if (user != null) {
      XMLWriter.writeXML(user, filePath);
    } else {
      System.out.println("User " + userName + " not found in the system.");
    }
  }

}
