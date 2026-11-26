import { SignedXml } from "xml-crypto";
import { DOMParser } from "@xmldom/xmldom";

export class WsSecuritySigner {
  private privateKeyPem: string;
  private publicCertPem: string;

  constructor(privateKeyPem: string, publicCertPem: string) {
    this.privateKeyPem = privateKeyPem;
    this.publicCertPem = publicCertPem;
  }

  // Wrap payload in signed SOAP Envelope
  signSoapEnvelope(actionName: string, bodyPayloadXml: string): string {
    const rawXml = `
      <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
        <soapenv:Header>
          <wsse:Security>
            <wsu:Timestamp wsu:Id="Timestamp-${Date.now()}">
              <wsu:Created>${new Date().toISOString()}</wsu:Created>
              <wsu:Expires>${new Date(Date.now() + 300000).toISOString()}</wsu:Expires>
            </wsu:Timestamp>
          </wsse:Security>
        </soapenv:Header>
        <soapenv:Body wsu:Id="Body-${Date.now()}">
          <${actionName}>
            ${bodyPayloadXml}
          </${actionName}>
        </soapenv:Body>
      </soapenv:Envelope>
    `.trim();

    const doc = new DOMParser().parseFromString(rawXml);
    const sig = new SignedXml();
    sig.signingKey = this.privateKeyPem;
    sig.signatureAlgorithm = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256";
    sig.canonicalizationAlgorithm = "http://www.w3.org/2001/10/xml-exc-c14n#";

    sig.addReference(
      "//*[local-name(.)='Body']",
      ["http://www.w3.org/2001/10/xml-exc-c14n#", "http://www.w3.org/2000/09/xmldsig#sha1"],
      "http://www.w3.org/2000/09/xmldsig#sha1"
    );

    sig.computeSignature(rawXml, {
      prefix: "ds",
      location: { reference: "//*[local-name(.)='Security']", action: "append" }
    });

    return sig.getSignedXml();
  }
}
