server.resource(
  "system-architecture-diagram",
  "diagram://architecture/core-mesh.png",
  { description: "Visual schematic of active microservice mesh", mimeType: "image/png" },
  async (uri) => {
    const imageBuffer = await fs.promises.readFile("assets/core-mesh.png");
    return {
      contents: [{
        uri: uri.href,
        blob: imageBuffer.toString("base64"),
        mimeType: "image/png"
      }]
    };
  }
);
