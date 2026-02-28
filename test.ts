// save this as fetch-users.ts

async function fetchUsers() {
  try {
    const url = 'http://localhost:1337/getUsers';
    
    // Make the API call
    const response = await fetch(url);
    
    // Check if the response is ok (status in the range 200-299)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    // Get the response data
    const data = await response.json();
    
    // Print the type of the data
    console.log('=== Response Type ===');
    console.log('Type:', Array.isArray(data) ? 'Array' : typeof data);
    
    // Print the actual data
    console.log('\n=== Response Data ===');
    console.log(JSON.stringify(data, null, 2));
    
    // Optional: If it's an array, show additional info
    if (Array.isArray(data)) {
      console.log(`\nArray length: ${data.length}`);
      if (data.length > 0) {
        console.log('First item type:', typeof data[0]);
        console.log('First item:', data[0]);
      }
    }
    
  } catch (error) {
    console.error('Error fetching users:', error);
  }
}

// Run the function
fetchUsers();
