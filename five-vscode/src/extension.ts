// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';

class FiveCodeAgentProvider implements vscode.WebviewViewProvider {
	public static readonly viewType = 'five-code-agent.panel';
	private extensionUri: vscode.Uri;

	constructor(extensionUri: vscode.Uri) {
		this.extensionUri = extensionUri;
	}

	public resolveWebviewView(
		webviewView: vscode.WebviewView,
		context: vscode.WebviewViewResolveContext,
		_token: vscode.CancellationToken,
	) {
		webviewView.webview.options = {
			enableScripts: true,
			localResourceRoots: [vscode.Uri.joinPath(this.extensionUri, 'webview-dist')]
		};

		this._getHtmlForWebview(webviewView.webview).then(html => {
			webviewView.webview.html = html;
		});
	}

	private async _getHtmlForWebview(webview: vscode.Webview): Promise<string> {
		const webviewDistPath = vscode.Uri.joinPath(this.extensionUri, 'webview-dist');
		
		const htmlPath = vscode.Uri.joinPath(webviewDistPath, 'index.html');
		const htmlContent = await this._getFileContent(htmlPath);
		
		if (!htmlContent) {
			return this._getFallbackHtml();
		}
		
		const modifiedHtml = this._modifyHtmlForWebview(htmlContent, webview, webviewDistPath);
		return modifiedHtml;
	}
	
	private async _getFileContent(uri: vscode.Uri): Promise<string | undefined> {
		try {
			const data = await vscode.workspace.fs.readFile(uri);
			return Buffer.from(data).toString();
		} catch {
			return undefined;
		}
	}
	
	private _modifyHtmlForWebview(html: string, webview: vscode.Webview, webviewDistPath: vscode.Uri): string {
		// Replace script and link tags to use webview.asWebviewUri
		return html.replace(
			/(src|href)="([^"]+)"/g,
			(match, attr, url) => {
				if (url.startsWith('http') || url.startsWith('data:')) {
					return match;
				}
				const localUri = vscode.Uri.joinPath(webviewDistPath, url);
				const webviewUri = webview.asWebviewUri(localUri);
				return `${attr}="${webviewUri}"`;
			}
		);
	}
	
	private _getFallbackHtml(): string {
		return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Five Code Agent</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 10px;
            margin: 0;
        }
        .content {
            text-align: center;
            padding: 20px;
        }
        h1 {
            color: var(--vscode-editor-foreground);
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="content">
        <h1>React app not found. Please build the webview first.</h1>
    </div>
</body>
</html>`;
	}
}

export function activate(context: vscode.ExtensionContext) {
	console.log('Congratulations, your extension "five-code-agent" is now active!');

	const provider = new FiveCodeAgentProvider(context.extensionUri);

	context.subscriptions.push(
		vscode.window.registerWebviewViewProvider(FiveCodeAgentProvider.viewType, provider)
	);

	const disposable = vscode.commands.registerCommand('five-code-agent.helloWorld', () => {
		vscode.window.showInformationMessage('Hello World from five-code-agent!');
	});

	context.subscriptions.push(disposable);
}

export function deactivate() {}
