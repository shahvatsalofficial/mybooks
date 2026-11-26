function isEndpointSecured(operation: any, rootSecurity: any[]): boolean {
  if (operation.security) {
    return Array.isArray(operation.security) && operation.security.length > 0;
  }
  return Array.isArray(rootSecurity) && rootSecurity.length > 0;
}
