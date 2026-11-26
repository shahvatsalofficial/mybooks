import { soap } from "strong-soap";

export class SoapModernizationBridge {
  private soapClient: any = null;

  async loadWsdl(wsdlUrl: string): Promise<string[]> {
    return new Promise((resolve, reject) => {
      soap.createClient(wsdlUrl, {}, (err: any, client: any) => {
        if (err) return reject(new Error(`WSDL Parsing Failure: ${err.message}`));
        this.soapClient = client;

        // Inspect available services and port operations
        const description = client.describe();
        const operations: string[] = [];

        for (const [serviceName, service] of Object.entries(description)) {
          for (const [portName, port] of Object.entries(service as any)) {
            for (const opName of Object.keys(port as any)) {
              operations.push(`${opName}`);
            }
          }
        }

        resolve(operations);
      });
    });
  }

  async invokeSoapOperation(operationName: string, args: Record<string, any>): Promise<any> {
    if (!this.soapClient) throw new Error("SOAP client not initialized.");

    return new Promise((resolve, reject) => {
      const method = this.soapClient[operationName];
      if (typeof method !== "function") {
        return reject(new Error(`SOAP operation '${operationName}' not found in WSDL.`));
      }

      method(args, (err: any, result: any, rawEnvelope: string) => {
        if (err) return reject(new Error(`SOAP Fault (${err.response?.status}): ${err.message}`));
        resolve(result);
      });
    });
  }
}
