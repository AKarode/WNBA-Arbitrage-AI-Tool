package model;

import java.io.IOException;
import java.util.stream.Collectors;

/**
 * The TextView class is responsible for generating a textual representation of a user's schedule.
 * It utilizes the {@code Appendable} interface to construct the schedule's output, allowing for
 * flexible output destinations such as {@code StringBuilder}, {@code StringBuffer}, or even direct
 * output streams like {@code System.out}.
 */
public class TextView {

  private static final String[] DAYS_OF_THE_WEEK = {
      "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
  };

  /**
   * Builds a textual representation of the schedule for a given user and appends it to the provided
   * {@code Appendable} object. The schedule is organized
   * by days of the week, with events listed under
   * their corresponding day including details such
   * as name, time, location, online status, and invitees.
   *
   * @param user       The user whose schedule is to be built.
   * @param appendable The {@code Appendable} object where the schedule will be appended.
   *                   This allows for outputting the schedule to various destinations.
   */
  public static void buildUserSchedule(User user, Appendable appendable) {
    try {
      appendable.append("User: ").append(user.getName()).append("\n");
      for (String day : DAYS_OF_THE_WEEK) {
        appendable.append(day).append(":\n");
        user.getSchedule().getEvents().stream()
            .filter(event -> event.getStartDay().equals(day))
            .forEach(event -> {
              try {
                appendable.append("\tname: ").append(event.getName()).append("\n")
                    .append("\ttime: ").append(event.getStartDay()).append(": ")
                    .append(event.getStartTime())
                    .append(" -> ").append(event.getEndDay())
                    .append(": ").append(event.getEndTime()).append("\n")
                    .append("\tlocation: ").append(event.getLocation()).append("\n")
                    .append("\tonline: ")
                    .append(String.valueOf(event.getOnlineStatus())).append("\n")
                    .append("\tinvitees: ");
                String invitees = event.getInvitedUsers().stream().map(u -> u.getName())
                    .collect(Collectors.joining(", "));
                appendable.append(invitees).append("\n\n");
              } catch (IOException e) {
                e.printStackTrace();
              }
            });
      }
    } catch (IOException e) {
      e.printStackTrace();
    }
  }

  /**
   * Renders the content of an {@code Appendable} object to the standard output. This method
   * is mainly used for debugging or console output purposes.
   *
   * @param appendable The {@code Appendable} object whose
   *                   content is to be rendered to the standard output.
   */
  public static void render(Appendable appendable) {
    try {
      System.out.println(appendable.toString());
    } catch (Exception e) {
      e.printStackTrace();
    }
  }


}
