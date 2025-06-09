package view;

import model.Event;
import model.ReadOnlyPlannerModel;
import model.User;

import javax.swing.*;
import java.awt.*;


/**
 * EventFrame provides a user interface for creating,
 * modifying, and viewing details of an event.
 * It extends JFrame and implements the PopUpFrame interface,
 * allowing for operations on Event objects
 * within a graphical interface. Users can input event details,
 * invite other users, and indicate whether
 * the event is online or in-person.
 */
public class EventFrame extends JFrame implements PopUpFrame {

  private final ReadOnlyPlannerModel model;
  private Event event;
  private JTextField eventNameField;
  private JTextField locationField;
  private JCheckBox isOnlineCheckbox;
  private JComboBox<String> startingDayCombo;
  private JTextField startingTimeField;
  private JComboBox<String> endingDayCombo;
  private JTextField endingTimeField;

  /**
   * Constructs an EventFrame window either with
   * a pre-existing Event object for editing
   * or without one for creating a new event.
   *
   * @param event The event to edit, or null if creating a new event.
   */
  public EventFrame(Event event, ReadOnlyPlannerModel model) {
    this.event = event;
    this.model = model;
    createAndShowGUI();
  }

  private void createAndShowGUI() {
    setTitle("Event Details");
    setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
    setLayout(new BoxLayout(getContentPane(), BoxLayout.Y_AXIS));
    JList<String> usersList = extractedShowGui();
    usersList.setSelectionMode(ListSelectionModel.MULTIPLE_INTERVAL_SELECTION);
    JScrollPane usersScrollPane = new JScrollPane(usersList);
    JButton createEventButton = new JButton("Create event");
    JButton modifyEventButton = new JButton("Modify event");
    JButton removeEventButton = new JButton("Remove event");
    createEventButton.addActionListener(e -> {
      if (validateInput()) {
        System.out.println("Create event: "
            + "Name: " + eventNameField.getText() + ", Location: " + locationField.getText()
            + ", Is Online: " + isOnlineCheckbox.isSelected()
            + ", Starting Day: " + startingDayCombo.getSelectedItem()
            + ", Starting Time: " + startingTimeField.getText()
            + ", Ending Day: " + endingDayCombo.getSelectedItem()
            + ", Ending Time: " + endingTimeField.getText());
      } else {
        System.out.println("Error: Please fill in all event details before creating.");
      }
    });
    removeEventButton.addActionListener(e -> {
      System.out.println("Remove event: "
          + "Name: " + eventNameField.getText()
          + ", Location: " + event.getLocation()
          + ", Is Online: " + event.getOnlineStatus()
          + ", Starting Day: " + event.getStartDay()
          + ", Starting Time: " + event.getStartTime()
          + ", Ending Day: " + event.getEndDay()
          + ", Ending Time: " + event.getEndTime());
    });
    setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
    add(createLabeledField("Event name:", eventNameField));
    add(createLabeledField("Location:", locationField));
    add(isOnlineCheckbox);
    add(createLabeledField("Starting Day:", startingDayCombo));
    add(createLabeledField("Starting time:", startingTimeField));
    add(createLabeledField("Ending Day:", endingDayCombo));
    add(createLabeledField("Ending time:", endingTimeField));
    add(new JLabel("Available users"));
    add(usersScrollPane);
    add(createEventButton);
    add(modifyEventButton);
    add(removeEventButton);
    pack();
    setVisible(true);
  }

  private JList<String> extractedShowGui() {
    eventNameField = new JTextField(event != null ? event.getName() : "");
    locationField = new JTextField(event != null ? event.getLocation() : "");
    isOnlineCheckbox = new JCheckBox("Is online", event != null && event.getOnlineStatus());
    startingDayCombo = new JComboBox<>(new String[]
        {"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"});
    startingDayCombo.setSelectedItem(event != null ? event.getStartDay() : "Sunday");
    startingTimeField = new JTextField(event != null ? event.getStartTime() : "");
    endingDayCombo = new JComboBox<>(new String[]
        {"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"});
    endingDayCombo.setSelectedItem(event != null ? event.getEndDay() : "Sunday");
    endingTimeField = new JTextField(event != null ? event.getEndTime() : "");
    String[] userListArray = event != null ? event.getInvitedUsers().stream()
        .map(User::getName).toArray(String[]::new) : new String[]{};
    JList<String> usersList = new JList<>(userListArray);
    return usersList;
  }

  private boolean validateInput() {
    // Validation logic remains the same
    return !eventNameField.getText().trim().isEmpty()
        && !locationField.getText().trim().isEmpty()
        && !startingTimeField.getText().trim().isEmpty()
        && !endingTimeField.getText().trim().isEmpty();
  }

  private JPanel createLabeledField(String labelText, JComponent field) {
    // This method remains the same
    JPanel panel = new JPanel();
    panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
    JLabel label = new JLabel(labelText);
    label.setAlignmentX(Component.LEFT_ALIGNMENT);
    field.setAlignmentX(Component.LEFT_ALIGNMENT);
    panel.add(label);
    panel.add(field);
    return panel;
  }

  /**
   * Renders the EventFrame GUI, making it visible to the user.
   * This method is intended
   * to ensure that the GUI is displayed on the Event
   * Dispatch Thread (EDT) for thread safety.
   */
  public void render() {
    SwingUtilities.invokeLater(() -> {
      new EventFrame(event,model).setVisible(true);
    });
  }

}
