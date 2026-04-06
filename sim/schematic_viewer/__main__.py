from sim.schematic_viewer.app import create_app

app = create_app()

if __name__ == "__main__":
    print("Schematic viewer: http://127.0.0.1:8765")
    app.run(host="127.0.0.1", port=8765, debug=False)
