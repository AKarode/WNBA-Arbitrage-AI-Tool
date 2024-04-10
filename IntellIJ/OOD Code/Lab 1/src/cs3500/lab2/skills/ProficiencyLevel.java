package cs3500.lab2.skills;

public enum ProficiencyLevel implements Skill {
  beginner,
  intermediate,
  expert;

  @Override
  public boolean satisfiesReq(Skill requirement) {
    if (this == expert) {
      return true;
    } else {
      return false;
    }

  }
}
