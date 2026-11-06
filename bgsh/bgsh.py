import cmd
import shlex
import uuid

from brewtils import EasyClient, SystemClient
from brewtils.config import load_config


class BGCLIShell(cmd.Cmd):
    intro = """
         ----  ------------           
      -----------------------         
     -------------------------        
    -------------------------------   
  ----------------------------------  
------------------------------------- 
------------------------------------- 
-----------=---=   ----  -----------  
 -----=+** === == ===   ==++=----     
     *****   ============ *********   
     *****     ====       *********** 
     *****     ====       *****    ***
     *****     =====      *****    ***
     *****     =====      *****    ***
     *****     =====      *****    ***
     *****     =====      *****    ***
     *****     =====      *********** 
     *****     =====      ********    
      ************************        
       **********************                   
Welcome to the Beer Garden interactive shell. Type help or ? to list commands.\n

"""
    prompt = "bgsh> "

    targetNamespace = None
    bg_config = {"bg_host": "localhost", "bg_port": 2337, "ssl_enabled": False}
    session = None

    def _parse_kwargs(self, arg_string):
        """Helper to parse a string like 'a=1 b="hello world"' into a dict."""
        kwargs = {}
        # shlex safely splits strings by spaces while respecting quotes
        try:
            tokens = shlex.split(arg_string)
        except ValueError as e:
            print(f"Error parsing arguments: {e}")
            return None

        for token in tokens:
            if "=" in token:
                key, value = token.split("=", 1)
                kwargs[key] = value
            else:
                print(
                    f"Warning: Ignoring invalid argument format '{token}'. Use key=value."
                )

        return kwargs

    def do_bg_set_config(self, arg):
        """
        Set config values for connecting to Beer Garden. Usage: bg_set_config bg_host=localhost bg_port=2337 ssl_enabled=false

        Options:
        bg_host (str): Beer-garden hostname
        bg_port (int): Beer-garden port
        bg_url_prefix (str): URL path that will be used as a prefix when communicating
            with Beer-garden. Useful if Beer-garden is running on a URL other than '/'.
        ssl_enabled (bool): Whether to use SSL for Beer-garden communication
        ca_cert (str): Path to certificate file containing the certificate of the
            authority that issued the Beer-garden server certificate
        ca_verify (bool): Whether to verify Beer-garden server certificate
        client_cert (str): Path to client certificate to use when communicating with
            Beer-garden
        """
        kwargs = self._parse_kwargs(arg)
        if kwargs is None:
            return

        # Extract values with sensible defaults
        if self.bg_config is None:
            self.bg_config = {}
        if "bg_host" in kwargs:
            self.bg_config["bg_host"] = kwargs.get("bg_host", None)

        if "bg_port" in kwargs:
            self.bg_config["bg_port"] = int(kwargs.get("bg_port", "2337"))

        if "bg_url_prefix" in kwargs:
            self.bg_config["bg_url_prefix"] = kwargs.get("bg_url_prefix", None)

        if "ssl_enabled" in kwargs:
            self.bg_config["ssl_enabled"] = (
                kwargs.get("ssl_enabled", "false").lower() == "true"
            )

        if "ca_cert" in kwargs:
            self.bg_config["ca_cert"] = kwargs.get("ca_cert", None)

        if "ca_verify" in kwargs:
            self.bg_config["ca_verify"] = (
                kwargs.get("ca_verify", "false").lower() == "true"
            )

        if "client_cert" in kwargs:
            self.bg_config["client_cert"] = kwargs.get("client_cert", None)

    def do_bg_load_env_config(self, arg):
        """Load Configuration from environment variables"""
        self.bg_config = load_config()

    def do_bg_ls(self, arg):
        """Lists the available Namespaces"""

        systems = EasyClient(**self.bg_config).find_systems(name="CLI")

        if len(systems) == 0:
            print("No available CLI clients")

        elif len(systems) == 1:
            print(f"CLI Client found {systems[0].namespace}, setting to default")
            self.do_bg_set_client(systems[0].namespace)
        else:
            print("Available CLI Clients")
            for system in systems:
                print(f"    - {system.namespace}")

    def do_bg_set_client(self, arg):
        """Set Target Client. Usage bg_set_client default"""

        self.targetNamespace = arg
        self.do_bg_create_session("")

    def do_bg_close_session(self, _):
        """Close Current Session"""
        if self.session is not None:
            try:
                SystemClient(
                    system_namespace=self.targetNamespace,
                    system_name="CLI",
                    **self.bg_config,
                ).stop_subprocess(subprocess_label=self.session)
            except:
                print("Failed to close current session")
        self.session = None

    def do_bg_create_session(self, _):
        """Create new session"""
        self.do_bg_close_session("")

        self.session = str(uuid.uuid4())
        SystemClient(
            system_namespace=self.targetNamespace, system_name="CLI", **self.bg_config
        ).start_subprocess(subprocess_label=self.session)

    def do_exit(self, _):
        """Exits the shell."""
        self.do_bg_close_session("")
        print("Goodbye!")
        return True  # Returning True stops the loop

    def default(self, line):
        """Handles any input that doesn't trigger an explicit do_* method."""
        # print(f"Generic handler caught: {line}")

        if self.targetNamespace is None:
            print("No Target Namespace Selected, please use bg_set_ns")

        else:
            response = SystemClient(
                system_namespace=self.targetNamespace,
                system_name="CLI",
                blocking=True,
                **self.bg_config,
            ).run_command(subprocess_label=self.session, cmd=line)
            if response.status == "SUCCESS":
                print(response.output)
            else:
                print(response.error_class)


if __name__ == "__main__":
    BGCLIShell().cmdloop()
