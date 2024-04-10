package model;

/**
 * Represents a user with a name and a personal schedule. The User class holds information about the
 * user and manages their schedule.
 */
public class User {

  private String name;
  private Schedule schedule;

  public User(User other) {
    this.name = other.name;
    this.schedule = new Schedule(other.schedule);
  }

  public User(String name) {
    this.name = name;
    this.schedule = new Schedule(this);
  }

  @Override
  public String toString() {
    return this.name;
  }

  public String getName() {
    return this.name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Schedule getSchedule() {
    return this.schedule;
  }

  public void setSchedule(Schedule newSchedule) {
    this.schedule = newSchedule;
  }
}
