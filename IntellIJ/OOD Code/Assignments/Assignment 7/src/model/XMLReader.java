package model;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import java.io.File;
import java.util.ArrayList;
import java.util.List;

/**
 * A utility class for reading user and event information from an XML file.
 * This class parses the XML file to create a User object that includes a schedule of events.
 */
public class XMLReader {

  /**
   * Reads user and event information from an XML file and creates a User object.
   * The User object includes a schedule populated with events defined in the XML.
   * Each event includes details such as name, location, timing, and a list of invited users.
   *
   * @param path    The file path of the XML document to be read.
   * @return        A User object representing the schedule owner,
   *                including their schedule populated with events.
   * @throws RuntimeException if an error occurs during XML parsing or processing.
   */

  public static User readXML(String path) {
    try {
      File xmlFile = new File(path);
      DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
      DocumentBuilder builder = factory.newDocumentBuilder();
      Document document = builder.parse(xmlFile);
      document.getDocumentElement().normalize();

      // Extract the schedule's user ID and create the user
      String userId = document.getDocumentElement().getAttribute("id");
      User scheduleOwner = new User(userId);

      // Initialize the user's schedule if needed
      scheduleOwner.setSchedule(new Schedule(scheduleOwner));

      NodeList eventList = document.getElementsByTagName("event");

      for (int i = 0; i < eventList.getLength(); i++) {
        Node node = eventList.item(i);
        if (node.getNodeType() == Node.ELEMENT_NODE) {
          Element element = (Element) node;

          String name = element.getElementsByTagName("name").item(0).getTextContent();
          String startDay = element.getElementsByTagName("start-day").item(0).getTextContent();
          String startTime = element.getElementsByTagName("start").item(0).getTextContent();
          String endDay = element.getElementsByTagName("end-day").item(0).getTextContent();
          String endTime = element.getElementsByTagName("end").item(0).getTextContent();
          boolean online = Boolean.parseBoolean(element.getElementsByTagName("online")
              .item(0).getTextContent());
          String location = element.getElementsByTagName("place").item(0).getTextContent();

          List<User> invitedUsers = new ArrayList<>();
          NodeList uidNodes = element.getElementsByTagName("uid");
          for (int j = 0; j < uidNodes.getLength(); j++) {
            invitedUsers.add(new User(uidNodes.item(j).getTextContent()));
          }

          // Create the event and add it to the user's schedule
          Event newEvent = new Event(name, location, online, startDay, startTime,
              endDay, endTime, scheduleOwner, invitedUsers);
          scheduleOwner.getSchedule().addEvent(newEvent);
        }
      }

      return scheduleOwner;
    } catch (Exception e) {
      e.printStackTrace();
      throw new RuntimeException("Failed to read XML", e);
    }
  }
}
