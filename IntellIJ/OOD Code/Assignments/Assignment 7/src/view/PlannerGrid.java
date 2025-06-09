package view;


/**
 * The PlannerGrid interface defines the essential
 * functionality for components
 * that display a planner or calendar
 * grid within the application. Implementing
 * this interface requires the ability to render
 * the planner or calendar component
 * visually in the user interface.
 */
public interface PlannerGrid {
  /**
   * Renders the planner or calendar grid component. This method should be implemented
   * to initialize and display the GUI elements of
   * the planner grid, such as drawing
   * the grid itself, populating it with data, and
   * setting up any necessary event listeners.
   * The specific implementation will depend
   * on the GUI framework being used (e.g., Swing).
   */
  public void render();
}
