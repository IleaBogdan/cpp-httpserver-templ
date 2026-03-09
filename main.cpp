#include"libs.h"

const std::string DATABASE_PATH="test.db";
sqlite3* db;
sqlite3_stmt* stmt;

std::string get_random_number(void){
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(1, 100);
    
    return std::to_string(dis(gen));
}
json check_user_in_db(int id){
    sqlite3_stmt* stmt;  // Local statement variable
    std::string sql = "SELECT * FROM users WHERE ID = @Id;";
    
    sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, 0);
    int index = sqlite3_bind_parameter_index(stmt, "@Id");
    sqlite3_bind_int(stmt, index, id);

    json result;  // Create json object to return
    
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        // Get the actual data from the query
        int id = sqlite3_column_int(stmt, 0);  // First column (ID)
        const char* name = (const char*)sqlite3_column_text(stmt, 1);  // Second column (Name)
        const char* email = (const char*)sqlite3_column_text(stmt, 2);  // Third column (Email)
        
        // Put the actual data into the json
        result = json({
            {"ID", id},
            {"Name", name},
            {"EMAIL", email}
        });
    }
    
    sqlite3_finalize(stmt);  // Clean up
    return result;
}
json check_user_in_db(std::string name){
    sqlite3_stmt* stmt;  // Local statement variable
    std::string sql = "SELECT * FROM users WHERE Name = @Name;";
    
    sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, 0);
    int index = sqlite3_bind_parameter_index(stmt, "@Name");
    sqlite3_bind_text(stmt, index, name.c_str(),-1, SQLITE_TRANSIENT);

    json result;  // Create json object to return
    
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        // Get the actual data from the query
        int id = sqlite3_column_int(stmt, 0);  // First column (ID)
        const char* name = (const char*)sqlite3_column_text(stmt, 1);  // Second column (Name)
        const char* email = (const char*)sqlite3_column_text(stmt, 2);  // Third column (Email)
        
        // Put the actual data into the json
        result = json({
            {"ID", id},
            {"Name", name},
            {"EMAIL", email}
        });
    }
    
    sqlite3_finalize(stmt);  // Clean up
    return result;
}
signed main(){
    signed STATUS_CODE=0;

    crow::SimpleApp app;
    // Add CORS to each route instead
    auto add_cors = [](crow::response& res) {
        res.add_header("Access-Control-Allow-Origin", "*");
        res.add_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
        res.add_header("Access-Control-Allow-Headers", "Content-Type, Authorization");
    };

    
    int rc=sqlite3_open(DATABASE_PATH.c_str(),&db);
    if(rc){
        std::cerr<<"failed to open db";
        goto RET;
    }

    CROW_ROUTE(app, "/").methods("GET"_method)([](crow::request& req, crow::response& res) {
        res.redirect("/static/swagger/index.html");
        res.end();
    });

    CROW_ROUTE(app, "/downloaddatabase").methods("GET"_method)([](crow::request& req, crow::response& res) {
        // Open the database file
        std::ifstream file(DATABASE_PATH, std::ios::binary);
        if (!file.is_open()) {
            res.code = 404;
            res.body = "Database file not found";
            res.end();
            return;
        }
        // Read the file contents
        std::stringstream buffer;
        buffer << file.rdbuf();
        // Set headers for file download
        res.add_header("Content-Type", "application/octet-stream");
        res.add_header("Content-Disposition", "attachment; filename=\"database.db\"");
        res.add_header("Access-Control-Allow-Origin", "*");
        
        // Send the file
        res.body = buffer.str();
        res.end();
    });

    CROW_ROUTE(app,"/checkUser").methods("GET"_method)([](crow::request& req, crow::response& res){
        auto paramId=req.url_params.get("id");
        if(!paramId){
            res.body="id parameter missing!";
            res.code=400;
            res.end();
        }
        auto data=check_user_in_db(std::stoi(paramId));
        res.set_header("Content-Type", "application/json");
        res.add_header("Access-Control-Allow-Origin", "*");
        res.body=data.dump(); 
        res.code=200;
        res.end();
    });

    CROW_ROUTE(app,"/checkName").methods("POST"_method)([](crow::request& req, crow::response& res){
        auto body_json=crow::json::load(req.body);
        if (!body_json) {
            res.code = 400;
            res.body = "Invalid body JSON";
            res.end();
            return;
        }
        std::string name=body_json["Name"].s();
        res.set_header("Content-Type", "application/json");
        res.add_header("Access-Control-Allow-Origin", "*");
        
        auto data=check_user_in_db(name);
        res.body = data.dump();
        res.code = 200;
        res.end();
    });
    
    CROW_ROUTE(app, "/random").methods("GET"_method)([](crow::request& req, crow::response& res){
        res.add_header("Access-Control-Allow-Origin", "*");
        res.body=get_random_number();
        res.code=200;
        res.end();
    });
    
    app.bindaddr("0.0.0.0").port(6969).multithreaded().run();
    
    END_PROCESSES:
    sqlite3_finalize(stmt);
    sqlite3_close(db);
    
    RET:
    return STATUS_CODE;
}