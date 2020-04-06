#!flask/bin/python
from app import app
import os, sys

if (os.environ.get("DEBUG", False) == "True"):
    app.config["DEBUG"] = True

    port = int(os.environ.get("PORT", 80))
    # port = process.env.PORT || 80
    # const PORT = process.env.PORT || 5001;

    app.listen(PORT, () => console.log(`Server is listening on port ${PORT}...`));

    print >> sys.stderr, "DEBUG Mode! Port: " + str(port)
    app.run(host="0.0.0.0", port=port, debug=True)

    #app.run(debug=True)
else:
    app.run()
