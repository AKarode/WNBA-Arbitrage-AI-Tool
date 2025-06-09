package model;

/**
 * The IScheduler interface defines the operations for scheduling and managing events,
 * as well as adding, removing, and retrieving users within a scheduling system. It provides
 * methods to manipulate user entries and events effectively.
 */
public interface PlannerModel extends ReadOnlyPlannerModel {
  void addUser(User u);

  void removeUser(User u);

  User getUser(String name);

  void createEvent(Event e);

}
