package controller;

import model.Event;
import model.User;

import java.io.File;
import java.util.List;

public interface Features {

  /**
   * Adds a user and their schedule to the system from an XML file.
   * @param xmlFile The XML file containing the user's schedule.
   */
  void addUser(File xmlFile);

  /**
   * Saves all schedules in the system to XML files in a specified directory.
   * @param directory The directory where the XML files should be saved.
   */
  void saveSchedules(File directory);

  /**
   * Creates a new event.
   * @param details The details of the event to create.
   */
  void createEvent(String name, String location, boolean onlineStatus, String startDay,
                   String startTime, String endDay, String endTime,
                   User host, List<User> invitedUsers);

  /**
   * Modifies an existing event.
   * @param eventId The ID of the event to modify.
   * @param newDetails The new event to replace the old event.
   */
  void modifyEvent(String eventId, Event newDetails);

  /**
   * Removes an event from the system.
   * @param eventId The ID of the event to remove.
   */
  void removeEvent(String eventId);

  /**
   * Opens the frame to create or modify an event.
   */
  void openEventFrame();

  /**
   * Switches the currently viewed user in the system.
   * @param userId The ID of the user to view.
   */
  void switchUser(String userId);
}
