from yapconf import YapconfSpec
import os

# Map this to your local Beer Garden Code
from beer_garden import config

my_spec = YapconfSpec(config._SPECIFICATION, env_prefix='BG_')

my_spec.generate_documentation(app_name="Beer Garden", output_file_name='bg_configuration_docs.md')

# This only works if you have Kramdoc installed via Ruby
# https://github.com/asciidoctor/kramdown-asciidoc
# gem install kramdown-asciidoc


os.system('kramdoc -output=config_yaml.adoc bg_configuration_docs.md')
