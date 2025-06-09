package model;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import org.w3c.dom.Document;
import org.w3c.dom.Element;


/**
 * The XMLWriter class is responsible for writing user schedule information to an XML file.
 * It generates an XML document from the schedule of a specified user and saves it to a file.
 */
public class XMLWriter {

  /**
   * Writes the schedule of a given user to an XML file at a specified file path.
   * The XML file will contain details of all events in the user's schedule,
   * including event names, start and end times, locations, and a list of invited users.
   *
   * @param user The user whose schedule is to be written to an XML file.
   * @param filePath The path of the file where the XML content will be saved.
   */
  public static void writeXML(User user, String filePath) {
    try {
      DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
      DocumentBuilder dBuilder = dbFactory.newDocumentBuilder();
      Document doc = dBuilder.newDocument();
      Element rootElement = doc.createElement("schedule");
      doc.appendChild(rootElement);
      rootElement.setAttribute("id", user.getName());
      for (Event event : user.getSchedule().getEvents()) {
        Element eventElement = doc.createElement("event");
        rootElement.appendChild(eventElement);
        Element name = doc.createElement("name");
        name.appendChild(doc.createTextNode(event.getName()));
        eventElement.appendChild(name);
        Element time = doc.createElement("time");
        eventElement.appendChild(time);
        createChildElement(doc, time, "start-day", event.getStartDay());
        createChildElement(doc, time, "start", event.getStartTime());
        createChildElement(doc, time, "end-day", event.getEndDay());
        createChildElement(doc, time, "end", event.getEndTime());
        Element location = doc.createElement("location");
        eventElement.appendChild(location);
        createChildElement(doc, location, "online", String.valueOf(event.getOnlineStatus()));
        createChildElement(doc, location, "place", event.getLocation());
        Element users = doc.createElement("users");
        eventElement.appendChild(users);
        for (User invitedUser : event.getInvitedUsers()) {
          createChildElement(doc, users, "uid", invitedUser.getName());
        }
      }
      TransformerFactory transformerFactory = TransformerFactory.newInstance();
      Transformer transformer = transformerFactory.newTransformer();
      transformer.setOutputProperty(OutputKeys.INDENT, "yes");
      DOMSource source = new DOMSource(doc);
      StreamResult result = new StreamResult(new java.io.File(filePath));
      transformer.transform(source, result);
    } catch (Exception e) {
      e.printStackTrace();
    }
  }

  /**
   * Creates a child element with the specified tag name and text content,
   * and appends it to the given parent element.
   * This is a utility method to simplify the process of adding elements to the DOM.
   *
   * @param doc The Document object to which the new element will be added.
   * @param parent The parent Element to which the new child element will be appended.
   * @param tagName The tag name for the new element.
   * @param textContent The text content for the new element.
   */
  private static void createChildElement(Document doc, Element parent,
                                         String tagName, String textContent) {
    Element element = doc.createElement(tagName);
    element.appendChild(doc.createTextNode(textContent));
    parent.appendChild(element);
  }
}
