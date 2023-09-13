<script>
    function updateData() {
        fetch('/update')
            .then(response => response.json())
            .then(data => {
                // Update the table with new data
                // You can use JavaScript to manipulate the DOM here
            });
    }

    // Call updateData() every few seconds
    setInterval(updateData, 5000); // Update every 5 seconds
</script>
