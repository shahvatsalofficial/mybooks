// Initial API layout (commonly in a baseline SDK package)
interface EnterpriseClient {
    clientId: string;
    connect(timeout: number): boolean;
}

// Second layout declared locally in an application plugin
interface EnterpriseClient {
    sessionToken: string;
    // Overloaded signature. This signature takes precedence during resolution
    connect(timeout: number, retryOnFail: boolean): Promise<boolean>;
}

// Validating compiler lookup ordering
class ProductionClient implements EnterpriseClient {
    public clientId: string = "CLI_101";
    public sessionToken: string = "TOK_A7B9";

    // Implementation must safely handle all overloaded paths
    public connect(timeout: number, retryOnFail?: boolean): any {
        if (retryOnFail !== undefined) {
            return Promise.resolve(true);
        }
        return true;
    }
}
