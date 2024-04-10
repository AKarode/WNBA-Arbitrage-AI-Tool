package model;

import java.util.List;
import java.util.Map;

/**
 * Represents an event with details such as its name, location, timing, and participants.
 * Supports events that are either online or in-person and ensures that event timings are valid
 * and within a single week.
 */
public class Event {

  private static final Map<String, Integer> DAY_TO_INT = Map.of(
      "Monday", 1,
      "Tuesday", 2,
      "Wednesday", 3,
      "Thursday", 4,
      "Friday", 5,
      "Saturday", 6,
      "Sunday", 7
  );
  private static final int MINUTES_IN_A_WEEK = 7 * 24 * 60;
  private String name;
  private String location;
  private boolean onlineStatus;
  private String startTime;
  private String startDay;
  private String endTime;
  private String endDay;
  private User host;
  private List<User> invitedUsers;

  /**
   * Constructs a new Event with specified details.
   * Validates the timing of the event to ensure it is within a single week and times are valid.
   *
   * @param name         The name of the event.
   * @param location     The location of the event; can be a physical location or a URL if online.
   * @param onlineStatus True if the event is online, false otherwise.
   * @param startDay     The starting day of the week for the event.
   * @param startTime    The starting time of the event in HHMM format.
   * @param endDay       The ending day of the week for the event.
   * @param endTime      The ending time of the event in HHMM format.
   * @param host         The host of the event.
   * @param invitedUsers A list of users invited to the event.
   * @throws IllegalArgumentException if the timing is not valid or does not fall within a week.
   */
  public Event(String name, String location, boolean onlineStatus, String startDay,
               String startTime, String endDay, String endTime,
               User host, List<User> invitedUsers) {
    if (isValidTime(startTime) && isValidTime(endTime)
        && isWithinAWeek(startDay, startTime, endDay, endTime)) {
      this.name = name;
      this.location = location;
      this.onlineStatus = onlineStatus;
      this.startTime = startTime;
      this.endTime = endTime;
      this.startDay = startDay;
      this.endDay = endDay;
      this.host = host;
      this.invitedUsers = invitedUsers;
    } else {
      throw new IllegalArgumentException("Time is not valid");
    }
  }

  /**
   * Checks if a given time string in HHMM format is valid.
   *
   * @param time The time string to validate.
   * @return true if the time is valid, false otherwise.
   */
  private static boolean isValidTime(String time) {
    // Check if the string length is exactly 4
    if (time == null || time.length() != 4) {
      return false;
    }

    try {
      // Extract the hour and minute parts
      int hour = Integer.parseInt(time.substring(0, 2));
      int minute = Integer.parseInt(time.substring(2, 4));

      // Check if the hour is between 0 and 23 and the minute is between 0 and 59
      if (hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59) {
        return true;
      }
    } catch (NumberFormatException e) {
      // If parsing fails, the string is not valid
      return false;
    }

    // If any condition fails, return false
    return false;
  }

  /**
   * Determines if the event duration is within a single week and starts before it ends.
   *
   * @param startDay  The start day of the event.
   * @param startTime The start time of the event in HHMM format.
   * @param endDay    The end day of the event.
   * @param endTime   The end time of the event in HHMM format.
   * @return True if the event is within a week and starts before it ends, false otherwise.
   */
  private static boolean isWithinAWeek(String startDay,
                                       String startTime, String endDay, String endTime) {
    int startDayInt = DAY_TO_INT.get(startDay);
    int endDayInt = DAY_TO_INT.get(endDay);

    int startMinutes = (startDayInt - 1) * 24 * 60 + Integer.parseInt(startTime.substring(0, 2))
        * 60 + Integer.parseInt(startTime.substring(2, 4));
    int endMinutes = (endDayInt - 1) * 24 * 60 + Integer.parseInt(endTime.substring(0, 2))
        * 60 + Integer.parseInt(endTime.substring(2, 4));

    // Check if the event duration is within a week
    return endMinutes - startMinutes < MINUTES_IN_A_WEEK && endMinutes - startMinutes >= 0;
  }

  // Getters and Setters
  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public String getLocation() {
    return location;
  }

  public void setLocation(String location) {
    this.location = location;
  }

  public boolean getOnlineStatus() {
    return onlineStatus;
  }

  public void setOnlineStatus(boolean onlineStatus) {
    this.onlineStatus = onlineStatus;
  }

  public String getStartTime() {
    return startTime;
  }

  public void setStartTime(String startTime) {
    this.startTime = startTime;
  }

  public String getStartDay() {
    return startDay;
  }

  public void setStartDay(String startDay) {
    this.startDay = startDay;
  }

  public String getEndTime() {
    return endTime;
  }

  public void setEndTime(String endTime) {
    this.endTime = endTime;
  }

  public String getEndDay() {
    return endDay;
  }

  public void setEndDay(String endDay) {
    this.endDay = endDay;
  }

  public User getHost() {
    return host;
  }

  public void setHost(User host) {
    this.host = host;
  }

  public List<User> getInvitedUsers() {
    return invitedUsers;
  }

  public void setInvitedUsers(List<User> invitedUsers) {
    this.invitedUsers = invitedUsers;
  }

  /**
   * Checks if this event overlaps with another event.
   *
   * @param other The other event to compare with this event.
   * @return true if the events overlap, false otherwise.
   */
  public boolean isOverLapping(Event other) {
    int thisStart = DAY_TO_INT.get(this.startDay) * 2400 + Integer.parseInt(this.startTime);
    int thisEnd = DAY_TO_INT.get(this.endDay) * 2400 + Integer.parseInt(this.endTime);
    int otherStart = DAY_TO_INT.get(other.startDay) * 2400 + Integer.parseInt(other.startTime);
    int otherEnd = DAY_TO_INT.get(other.endDay) * 2400 + Integer.parseInt(other.endTime);


    return !(thisEnd <= otherStart || thisStart >= otherEnd);
  }


}
