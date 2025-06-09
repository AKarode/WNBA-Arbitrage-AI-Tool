package cs3500.samegame.model.hw02;

import java.io.IOException;
import java.util.List;

public class AutoMatchGame implements SameGameModel {
  @Override
  public void swap(int fromRow, int fromCol, int toRow, int toCol) {

  }

  @Override
  public void removeMatch(int row, int col) throws IOException {

  }

  @Override
  public int width() {
    return 0;
  }

  @Override
  public int length() {
    return 0;
  }

  @Override
  public Object pieceAt(int row, int col) {
    return null;
  }

  @Override
  public int score() {
    return 0;
  }

  @Override
  public int remainingSwaps() {
    return 0;
  }

  @Override
  public boolean gameOver() {
    return false;
  }

  @Override
  public void startGame(int rows, int cols, int swaps, boolean random) {

  }

  @Override
  public Object[] createListOfPieces() {
    return new Object[0];
  }

  @Override
  public void startGame(List board, int swaps) {

  }
}
