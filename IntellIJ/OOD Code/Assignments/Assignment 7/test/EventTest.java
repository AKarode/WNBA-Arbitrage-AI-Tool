import model.Event;
import model.User;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import java.util.ArrayList;
import java.util.List;

class EventTest {

  // Helper method to create a mock user
  private User createUser(String name) {
    return new User(name);
  }

  @Test
  void testEventsOverlap() {
    User host = createUser("Host");
    List<User> invitedUsers = new ArrayList<>();
    invitedUsers.add(createUser("User1"));
    invitedUsers.add(createUser("User2"));

    // Event 1: Monday 10:00 - 11:00
    Event event1 = new Event("Morning Meeting", "Office", false, "Monday",
        "1000", "Monday", "1100", host, invitedUsers);

    // Event 2: Overlaps with Event 1, same day, 10:30 - 12:00
    Event event2 = new Event("Extended Meeting", "Office", false, "Monday",
        "1030", "Monday", "1200", host, invitedUsers);

    assertTrue(event1.isOverLapping(event2), "Event1 should overlap with Event2");
  }

  @Test
  void testEventsDoNotOverlap() {
    User host = createUser("Host");
    List<User> invitedUsers = new ArrayList<>();
    invitedUsers.add(createUser("User1"));
    invitedUsers.add(createUser("User2"));

    // Event 1: Monday 10:00 - 11:00
    Event event1 = new Event("Morning Meeting", "Office", false, "Monday",
        "1000", "Monday", "1100", host, invitedUsers);

    // Event 3: Does not overlap with Event 1, same day, 11:00 - 12:00
    Event event3 = new Event("Afternoon Meeting", "Office", false, "Monday",
        "1100", "Monday", "1200", host, invitedUsers);

    assertFalse(event1.isOverLapping(event3), "Event1 should not overlap with Event3");
  }

  @Test
  void testEventOverlapAcrossDays() {
    User host = createUser("Host");
    List<User> invitedUsers = new ArrayList<>();
    invitedUsers.add(createUser("User1"));

    // Event 4: Sunday 23:00 - Monday 01:00
    Event event4 = new Event("Late Night Meeting", "Online", true,
        "Sunday", "2300", "Monday", "0100", host, invitedUsers);

    // Event 5: Starts right after Event 4 ends, no overlap, Monday 01:00 - 02:00
    Event event5 = new Event("Early Morning Meeting", "Online", true,
        "Monday", "0100", "Monday", "0200", host, invitedUsers);

    assertFalse(event4.isOverLapping(event5), "Event4 should not overlap with Event5");
  }
}
