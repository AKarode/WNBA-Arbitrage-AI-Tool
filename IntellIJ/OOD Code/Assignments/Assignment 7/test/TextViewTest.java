import model.Event;
import model.Schedule;
import model.TextView;
import model.User;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * The TextViewTest class is designed to validate the functionality of the TextView utility,
 * particularly focusing on its ability to correctly build and represent
 * a user's schedule in a textual format.
 * It sets up a controlled test environment with
 * predefined users and events, then compares the output
 * of the TextView's buildUserSchedule method against expected textual representations.
 * This class ensures that the scheduling and textual representation
 * logic works as intended for various scenarios,
 * including different event configurations and schedule compositions.
 */
public class TextViewTest {

  private User testUser;

  private StringBuilder appendable;

  @BeforeEach
  void setUp() {
    Event testEvent1;
    Event testEvent2;

    // Initialize user and events here
    testUser = new User("Test User");
    testUser.setSchedule(new Schedule(testUser)); // Assuming Schedule constructor takes a User

    // Initialize two events here
    testEvent1 = new Event("Test Event 1", "Location 1", true,
        "Monday", "0900", "Monday", "1000",
        testUser, List.of(testUser));

    testEvent2 = new Event("Test Event 2", "Location 2", false,
        "Tuesday", "1100", "Tuesday", "1200", testUser,
        List.of(testUser));

    // Add events to the user's schedule
    testUser.getSchedule().getEvents().add(testEvent1);
    testUser.getSchedule().getEvents().add(testEvent2);

    // Initialize the appendable
    appendable = new StringBuilder();
  }

  @Test
  void testBuildUserSchedule() throws IOException {
    // Build the user schedule
    TextView.buildUserSchedule(testUser, appendable);

    // Define the expected output
    String expected = "User: Test User\n" +
        "Sunday:\n" +
        "Monday:\n" +
        "\tname: Test Event 1\n" +
        "\ttime: Monday: 0900 -> Monday: 1000\n" +
        "\tlocation: Location 1\n" +
        "\tonline: true\n" +
        "\tinvitees: Test User\n\n" +
        "Tuesday:\n" +
        "\tname: Test Event 2\n" +
        "\ttime: Tuesday: 1100 -> Tuesday: 1200\n" +
        "\tlocation: Location 2\n" +
        "\tonline: false\n" +
        "\tinvitees: Test User\n\n" +
        "Wednesday:\n" +
        "Thursday:\n" +
        "Friday:\n" +
        "Saturday:\n";

    // Assert that the actual output matches the expected output
    TextView.render(appendable);
    assertEquals(expected, appendable.toString());
  }
}
