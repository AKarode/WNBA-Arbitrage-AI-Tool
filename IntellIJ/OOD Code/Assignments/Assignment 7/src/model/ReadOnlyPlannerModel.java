package model;

import java.util.List;


/**
 * The ReadOnlyPlannerModel interface defines the
 * read-only operations that can be performed on a planner model.
 * This interface is intended for scenarios where only viewing the
 * data is required, without the ability to modify it.
 * It provides methods to retrieve user information from the planner.
 */
public interface ReadOnlyPlannerModel {
  List<User> users = null;
  User getUser(String name);

  List<User> getUsers();



}
