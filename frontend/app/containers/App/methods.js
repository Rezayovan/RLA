import { createSelector } from "reselect";

export const getAuditMethods = () => {
  let list = ["one", "two", "three"];
  createSelector(list, list => list)
}