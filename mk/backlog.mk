backlog-browser:
	node ./node_modules/backlog.md/cli.js browser --port $$((RANDOM % 10000 + 1024))
.PHONY: backlog-browser

backlog: backlog-browser

# Copied from https://github.com/alvarogarcia7/testcase-generator/blob/98dab598dfa70fb0f661a063c25f62a659449a5e/mk/backlog.mk
