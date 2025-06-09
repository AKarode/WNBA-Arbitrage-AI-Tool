package model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Represents a schedule associated with a user. This class
 * allows for the management of events within
 * the user's schedule, including adding and removing events. It ensures that no
 * events overlap with
 * each other.
 */
public class Schedule {
  private User owner;
  private List<Event> events;

  //Deep Copy Constructor
  public Schedule(Schedule other) {
    this.owner = other.owner;
    this.events = new ArrayList<>(other.events);
  }

  public Schedule(User owner) {
    this.owner = owner;
    this.events = new ArrayList<>();
  }

  public User getOwner() {
    return owner;
  }

  public void setOwner(User owner) {
    this.owner = owner;
  }

  /**
   * Provides a read-only view of the events in the schedule.
   * This ensures that external modifications to the list
   * can't directly affect the internal list of events.
   *
   * @return A read-only List of events.
   */
  public List<Event> getEvents() {
    return Collections.unmodifiableList(events);
  }

  /**
   * Adds an event to the schedule, ensuring no overlap with existing events.
   *
   * @param e the event to add
   * @throws IllegalArgumentException if the
   *                                  event overlaps with any existing event
   */
  public void addEvent(Event e) {
    for (Event event : this.events) {
      if (event.isOverLapping(e)) {
        throw new IllegalArgumentException("Event overlaps with another event");
      }
    }
    this.events.add(e);
  }

  public void removeEvent(Event e) {
    this.events.remove(e);
  }
}
