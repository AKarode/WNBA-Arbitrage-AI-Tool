import model.CentralSystem;
import model.Event;
import model.User;
import org.junit.Before;
import org.junit.Test;

import java.io.File;
import java.util.Arrays;
import java.util.Collections;

import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;

/**
 * Test suite for the CentralSystem class.
 * Validates the functionality of user and event management within the system.
 */
public class CentralSystemTests {

  private CentralSystem centralSystem;
  private User user1;
  private User user2;
  private Event event1;

  @Before
  public void setUp() {
    centralSystem = new CentralSystem();
  }

  @Test
  public void addUser() {
    centralSystem.addUser(new User("Mahith"));
    assertEquals(centralSystem.getUsers().size(), 1);
  }

  @Test
  public void checkAddingTheSameUser() {
    centralSystem.addUser(new User("Mahith"));
    centralSystem.addUser(new User("Mahith"));
    assertEquals(centralSystem.getUsers().size(), 1);

  }

  @Test
  public void removeUser() {
    centralSystem.addUser(new User("Mahith"));
    centralSystem.addUser(new User("Suneet"));
    centralSystem.removeUser(new User("Suneet"));
    assertEquals(centralSystem.getUsers().size(), 1);
  }

  @Test
  public void removeUserThatDoestExist() {
    centralSystem.addUser(new User("Mahith"));
    centralSystem.addUser(new User("Suneet"));
    centralSystem.removeUser(new User("Bobby"));
    assertEquals(centralSystem.getUsers().size(), 2);
  }

  @Test
  public void gettingUser() {
    centralSystem.addUser(new User("Mahith"));
    centralSystem.addUser(new User("Suneet"));
    centralSystem.removeUser(new User("Bobby"));
    assertEquals(centralSystem.getUsers().size(), 2);
  }

  @Test(expected = IllegalArgumentException.class)
  public void testGettingNullUser() {
    centralSystem.addUser(new User("Mahith"));
    centralSystem.getUser(null);
  }

  @Test(expected = IllegalArgumentException.class)
  public void testingGetUser() {
    centralSystem.addUser(new User("Mahith"));
    centralSystem.getUser(null);
  }

  @Test
  public void testCreateEventAddsToHostAndInvitees() {
    User host = new User("Liam");
    User invitee = new User("Noah");
    centralSystem.addUser(host);
    centralSystem.addUser(invitee);
    Event event = new Event("Project Meeting", "Conference Room",
            false, "Thursday", "1400", "Thursday",
            "1600", host, Collections.singletonList(invitee));

    centralSystem.createEvent(event);

    assertTrue("Host should have the event in their schedule",
            host.getSchedule().getEvents().contains(event));
    assertTrue("Invitee should have the event in their schedule",
            invitee.getSchedule().getEvents().contains(event));
  }

  @Test
  public void getUserReturnsCorrectUser() {
    User expectedUser = new User("Olivia");
    centralSystem.addUser(expectedUser);

    User actualUser = centralSystem.getUser("Olivia");
    assertEquals("Should return the correct user", expectedUser, actualUser);
  }

  @Test(expected = IllegalArgumentException.class)
  public void getUserThrowsExceptionForNonexistentUser() {
    centralSystem.addUser(new User("Emma"));
    centralSystem.getUser("Ava"); // This should throw an exception
  }

  @Test
  public void updateEventModifiesEventDetails() {
    User host = new User("Sophia");
    centralSystem.addUser(host);
    Event originalEvent = new Event("Coding Session", "Library",
            true, "Monday", "1000", "Monday", "1200",
            host, Collections.emptyList());
    host.getSchedule().addEvent(originalEvent);

    Event updatedEvent = new Event("Intense Coding Session", "Online",
            true, "Monday", "1000", "Monday",
            "1300", host, Collections.emptyList());
    centralSystem.updateEvent(originalEvent, updatedEvent);

    assertFalse("Original event should be removed from the host's schedule",
            host.getSchedule().getEvents().contains(originalEvent));
    assertTrue("Updated event should be added to the host's schedule",
            host.getSchedule().getEvents().contains(updatedEvent));
    assertEquals("Updated event should have a new name",
            "Intense Coding Session", host.getSchedule().getEvents().get(0).getName());
    assertEquals("Updated event duration should be extended",
            "1300", host.getSchedule().getEvents().get(0).getEndDay());
  }

  // Correcting the test for removing a user that does not exist
  @Test
  public void removeUserThatDoesNotExistDoesNothing() {
    centralSystem.addUser(new User("Mia"));
    int initialSize = centralSystem.getUsers().size();

    try {
      centralSystem.removeUser(new User("Ella"));
      assertEquals("Removing a non-existing user should not change the users size",
              initialSize, centralSystem.getUsers().size());
    } catch (Exception e) {
      fail("Should not throw any exception when trying to remove a non-existing user");
    }
  }

  @Test
  public void testEventModificationReflectsOnAllInvitedUsers() {
    User host = new User("HostUser");
    User invitedUser = new User("InvitedUser");
    centralSystem.addUser(host);
    centralSystem.addUser(invitedUser);

    Event event = new Event("Team Meeting", "Office", true,
            "Tuesday", "0900", "Tuesday", "1000", host,
            Arrays.asList(invitedUser));
    centralSystem.createEvent(event);

    // Modify the event's time
    centralSystem.changeEventTiming("Team Meeting", "Tuesday",
            "1100", "Tuesday", "1200");

    // Verify that the event's new timing is reflected in the invited user's schedule as well
    assertTrue(invitedUser.getSchedule().getEvents()
        .stream().anyMatch(e -> e.getStartDay().equals("1100")
            && e.getEndTime().equals("1200")));
  }

  @Test
  public void testAutomaticEventScheduling() {
    // Assuming an implementation for automatic scheduling is added in the future
    // This test would simulate the scenario where the system suggests or schedule
    fail("Automatic event scheduling feature not implemented yet.");
  }

  @Test
  public void testEventRemovalUpdatesAllUsers() {
    User host = new User("EventHost");
    User guest = new User("EventGuest");
    centralSystem.addUser(host);
    centralSystem.addUser(guest);

    Event meeting = new Event("Important Meeting", "Conference Room",
            false, "Wednesday", "1500", "Wednesday", "1600", host, Arrays.asList(guest));
    centralSystem.createEvent(meeting);

    centralSystem.removeEvent(meeting);

    // Ensure the event is removed from both the host and the guest's schedules
    assertFalse(host.getSchedule().getEvents().contains(meeting));
    assertFalse(guest.getSchedule().getEvents().contains(meeting));
  }

  @Test
  public void testAddingUserUpdatesExistingEvents() {
    User existingUser = new User("ExistingUser");
    centralSystem.addUser(existingUser);

    Event publicEvent = new Event("Public Lecture", "Main Hall", true,
            "Monday", "1000", "Monday", "1200", existingUser,
            Arrays.asList(existingUser));
    centralSystem.createEvent(publicEvent);

    // Assuming a method to add users to existing events if not explicitly invited
    User newUser = new User("NewUser");

    // Verify newUser is now included in the event
    assertTrue(publicEvent.getInvitedUsers().contains(newUser));
  }

  @Test
  public void testXMLScheduleImportAndExport() {
    User user = new User("XMLUser");
    centralSystem.addUser(user);
    // Assuming you have methods to import and export user schedules to XML
    centralSystem.addUserFromXML("import.xml");
    centralSystem.exportUserScheduleToXML("XMLUser", "export.xml");


    // Consider using an XML comparison tool or library
    assertTrue(new File("path/to/export.xml").exists());
  }

  @Test(expected = IllegalArgumentException.class)
  public void testRejectEventAdditionDueToConflict() {
    User host = new User("HostUser");
    User guest = new User("GuestUser");
    centralSystem.addUser(host);
    centralSystem.addUser(guest);
    // Create an event and add it to the system
    Event initialEvent = new Event("Initial Meeting", "Room 101", false,
            "Wednesday", "0900", "Wednesday", "1000", host, Collections.singletonList(guest));
    centralSystem.createEvent(initialEvent);

    // Attempt to create a conflicting event
    Event conflictingEvent = new Event("Overlapping Meeting", "Room 102", true,
            "Wednesday", "0930", "Wednesday", "1030", guest, Collections.singletonList(host));
    centralSystem.createEvent(conflictingEvent);
  }




}
