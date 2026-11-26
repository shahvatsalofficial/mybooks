// Safe Boolean Parsing that avoids the "false" === true trap
const SafeBoolean = z.preprocess((val) => {
  if (typeof val === "string") {
    const cleaned = val.trim().toLowerCase();
    if (cleaned === "true" || cleaned === "1" || cleaned === "yes") return true;
    if (cleaned === "false" || cleaned === "0" || cleaned === "no") return false;
  }
  return val;
}, z.boolean());
