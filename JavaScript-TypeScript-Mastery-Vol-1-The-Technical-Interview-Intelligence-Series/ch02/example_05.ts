type StringOrNum = string | number;
type Checked = IsString<StringOrNum>; // Resolves to true | false (boolean!)
