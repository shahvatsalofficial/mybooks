import { Project, SyntaxKind } from "ts-morph";

export function updateMethodReturnStatement(
  filePath: string,
  className: string,
  methodName: string,
  newReturnExpression: string
): string {
  const project = new Project();
  const sourceFile = project.addSourceFileAtPath(filePath);

  const targetClass = sourceFile.getClass(className);
  if (!targetClass) {
    throw new Error(`AST_ERROR: Class '${className}' not found in ${filePath}`);
  }

  const targetMethod = targetClass.getMethod(methodName);
  if (!targetMethod) {
    throw new Error(`AST_ERROR: Method '${methodName}' not found in class '${className}'`);
  }

  // Locate the return statement within the method's AST node graph
  const returnStatement = targetMethod.getFirstDescendantByKind(SyntaxKind.ReturnStatement);
  if (!returnStatement) {
    throw new Error(`AST_ERROR: No return statement found in method '${methodName}'`);
  }

  // Surgically replace the return expression while preserving formatting
  returnStatement.replaceWithText(`return ${newReturnExpression};`);

  sourceFile.saveSync();
  return `Successfully updated AST node in ${className}.${methodName}`;
}
