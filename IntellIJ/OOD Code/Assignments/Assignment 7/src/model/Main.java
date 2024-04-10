package model;

//import view.CalendarUI;

import view.CalendarUI;

/**
 * Checks to make sure the application works as expected.
 */
public class Main {

  /**
   * The entry point of the application. It demonstrates the process of initializing the system,
   * reading a user's schedule from an XML file, adding the user to the central system, and
   * displaying the schedule.
   *
   * @param args Command-line arguments (not used).
   */
  public static void main(String[] args) {
    CentralSystem system = new CentralSystem();
    XMLReader reader = new XMLReader();
    User user = reader.readXML("src/model/input.xml");
    system.addUser(user);
    CalendarUI fortnite = new CalendarUI(system);

    fortnite.render();

  }

}