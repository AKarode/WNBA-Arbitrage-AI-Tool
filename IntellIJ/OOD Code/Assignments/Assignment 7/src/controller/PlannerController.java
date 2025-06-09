package controller;

import model.Event;
import model.ReadOnlyPlannerModel;
import model.User;
import view.CalendarUI;

import java.io.File;
import java.util.List;

public class PlannerController implements Features{
  private ReadOnlyPlannerModel model;
  private CalendarUI view;

    public PlannerController(ReadOnlyPlannerModel model, CalendarUI view) {
        this.model = model;
        this.view = view;
        this.view.setFeatures(this);
    }

  @Override
  public void addUser(File xmlFile) {

  }

  @Override
  public void saveSchedules(File directory) {

  }

  @Override
  public void createEvent(String name, String location, boolean onlineStatus, String startDay, String startTime, String endDay, String endTime, User host, List<User> invitedUsers) {


  }

  @Override
  public void modifyEvent(String eventId, Event newDetails) {

  }

  @Override
  public void removeEvent(String eventId) {

  }

  @Override
  public void openEventFrame() {

  }

  @Override
  public void switchUser(String userId) {

  }
}
