package view;

import controller.Features;
import model.Event;
import model.ReadOnlyPlannerModel;
import model.User;
import javax.swing.JMenuBar;
import javax.swing.JMenu;
import javax.swing.JMenuItem;
import javax.swing.JTable;
import javax.swing.JFrame;
import javax.swing.JButton;
import javax.swing.JPanel;
import javax.swing.JComboBox;
import javax.swing.BorderFactory;
import javax.swing.JScrollPane;
import javax.swing.JFileChooser;
import javax.swing.SwingUtilities;
import javax.swing.table.DefaultTableCellRenderer;
import java.awt.BorderLayout;
import java.awt.Component;
import java.awt.Color;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.util.HashMap;
import java.util.Map;

/**
 * The CalendarUI class provides a graphical user interface for displaying a calendar
 * with scheduled events. It allows users to view events
 * scheduled in the planner model,
 * create new events, and save the calendar to a file. This class extends JFrame and implements
 * the PlannerGrid interface for integration with
 * the application's model-view-controller architecture.
 */
public class CalendarUI extends JFrame implements PlannerGrid {

  private static final Map<String, Integer> DAY_TO_INT = Map.of(
      "Sunday", 1,
      "Monday", 2,
      "Tuesday", 3,
      "Wednesday", 4,
      "Thursday", 5,
      "Friday", 6,
      "Saturday", 7
  );


  private ReadOnlyPlannerModel model;
  private Features features;

  /**
   * Constructs a CalendarUI object with a reference to the ReadOnlyPlannerModel.
   *
   * @param model The read-only planner model used to retrieve user and event data.
   */
  public CalendarUI(ReadOnlyPlannerModel model) {
    this.model = model;
    System.out.println(model.users);
  }

  public void setFeatures(Features features) {
    this.features = features;
  }

  private HashMap<Integer, Event> printEvents() {

    HashMap<Integer, Event> timeToEvent = new HashMap<>();

    for (User u : model.getUsers()) {
      for (Event e : u.getSchedule().getEvents()) {
        System.out.println(e.getStartDay() + ", "
            + e.getStartTime() + " - " +  e.getEndDay() + ", " + e.getEndTime());

        int startDay = DAY_TO_INT.get(e.getStartDay()) - 1;
        int startHour = Integer.parseInt(e.getStartTime().substring(0, 2));
        int startMinutes = Integer.parseInt(e.getStartTime().substring(2, 4));
        int startTimeMinutes = startDay * 1440 + startHour * 60 + startMinutes;

        int endDay = DAY_TO_INT.get(e.getEndDay()) - 1;
        int endHour = Integer.parseInt(e.getEndTime().substring(0, 2));
        int endMinutes = Integer.parseInt(e.getEndTime().substring(2, 4));
        int endTimeMinutes = endDay * 1440 + endHour * 60 + endMinutes;

        if (endTimeMinutes > startTimeMinutes) {
          for (int i = startTimeMinutes; i <= endTimeMinutes; i++) {
            timeToEvent.put(i, e);
          }
        } else {
          for (int i = startTimeMinutes; i <= 10080; i++) {
            timeToEvent.put(i, e);
          }
        }
      }
    }
    return timeToEvent;
  }


  public void render() {

    SwingUtilities.invokeLater(() -> this.createAndShowGUI());
  }

  private void createAndShowGUI() {

    HashMap<Integer, Event> intEvent = this.printEvents();

    JFrame frame = new JFrame("Calendar");
    extractedShowGUI(frame);

    // Create a table to represent the calendar grid
    String[] columns = new String[]{"Sunday", "Monday", "Tuesday",
        "Wednesday", "Thursday", "Friday", "Saturday"};
    Object[][] data = new Object[1440][7]; // 1440 minutes in a day, 7 days a week
    JTable table = new JTable(data, columns);

    // Customize row height to make blocks smaller
    table.setRowHeight(2); // Example: setting the row height to 10 pixels

    table.setDefaultRenderer(Object.class, new DefaultTableCellRenderer() {
      @Override
      public Component getTableCellRendererComponent(JTable table, Object value,
                                                     boolean isSelected, boolean hasFocus,
                                                     int row, int column) {
        Component component =
            super.getTableCellRendererComponent(table, value, isSelected, hasFocus, row, column);

        //        calculate the time based on the row and column
        int currTime = column * 1440 + row;


        if (intEvent.containsKey(currTime)) {
          System.out.println(currTime);
          component.setBackground(Color.RED);
        } else {
          component.setBackground(Color.WHITE);
        }

        // Apply a light border for each hour and a strong border for every 4 hours
        if ((row + 1) % 240 == 0) { // Every 4 hours
          setBorder(BorderFactory.createMatteBorder(1, 1, 20, 1, Color.BLACK));
        } else if ((row + 1) % 60 == 0) { // Every hour
          setBorder(BorderFactory.createMatteBorder(1, 1, 1, 1, Color.GRAY));
        }
        return component;
      }
    });

    table.addMouseListener(new MouseAdapter() {
      public void mouseClicked(MouseEvent e) {
        int row = table.rowAtPoint(e.getPoint());
        int column = table.columnAtPoint(e.getPoint());
        int currTime = column * 1440 + row;
        Event clickedEvent = intEvent.get(currTime);
        if (clickedEvent != null) {
          EventFrame eventFrame = new EventFrame(clickedEvent, model);
          eventFrame.render();
        }
      }
    });


    frame.add(new JScrollPane(table), BorderLayout.CENTER);

    JButton createEventButton = new JButton("Create event");

    createEventButton.addActionListener(new ActionListener() {
      @Override
      public void actionPerformed(ActionEvent e) {
        EventFrame eventFrame = new EventFrame(null, model);
        eventFrame.render();
      }
    });

    // Create buttons and add them to a panel at the bottom
    JPanel buttonPanel = new JPanel();
    JComboBox<String> dropdownMenu =
        new JComboBox<>(this.model.getUsers()
            .stream().map(Object::toString).toArray(String[]::new));
    buttonPanel.add(dropdownMenu); // Add dropdown menu instead of "<none>" button
    buttonPanel.add(createEventButton);
    buttonPanel.add(new JButton("Schedule event"));
    frame.add(buttonPanel, BorderLayout.SOUTH);

    // Display the window
    frame.pack();
    frame.setSize(800, 600); // Adjust size as needed
    frame.setVisible(true);
  }

  private void extractedShowGUI(JFrame frame) {
    frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
    frame.setLayout(new BorderLayout());

    // Create a menu bar
    JMenuBar menuBar = new JMenuBar();
    JMenu fileMenu = new JMenu("File");

    // Create and add "Open Calendar" menu item
    JMenuItem openItem = new JMenuItem("Add calender");
    openItem.addActionListener(e -> {
    });
    fileMenu.add(openItem);

    JMenuItem saveItem = new JMenuItem("Save calendars");
    saveItem.addActionListener(this::saveCalendars);
    fileMenu.add(saveItem);


    menuBar.add(fileMenu);
    frame.setJMenuBar(menuBar);
  }

  private void saveCalendars(ActionEvent e) {
    JFileChooser fileChooser = new JFileChooser();
    fileChooser.setDialogTitle("Select directory to save schedules");
    fileChooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
    int returnValue = fileChooser.showSaveDialog(this);
    if (returnValue == JFileChooser.APPROVE_OPTION) {
      if (fileChooser.getSelectedFile().isDirectory()) {
        System.out.println("Schedules will be saved to: " + fileChooser.getSelectedFile());
      }
    }
  }


}
