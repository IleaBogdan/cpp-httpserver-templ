#include <crow.h>
#include <random>
#include <sqlite3.h>
#include <string>
#include <vector>
#include <algorithm>

#include "json.hpp"
using json=nlohmann::json;

const std::string DATABASE_PATH="test.db";
sqlite3* db;
sqlite3_stmt* stmt;

std::string get_random_number(void){
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(1, 100);
    
    return std::to_string(dis(gen));
}
json get_users_from_db(void){
    sqlite3_stmt* stmt;  // Local statement variable
    std::string sql = "SELECT * FROM users WHERE ID = @Id;";
    
    sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, 0);
    int index = sqlite3_bind_parameter_index(stmt, "@Id");
    sqlite3_bind_int(stmt, index, 1);

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
    
    // Add OPTIONS handler for preflight requests
    CROW_ROUTE(app, "/<path>").methods("OPTIONS"_method)([](std::string path){
        crow::response res(200);
        res.add_header("Access-Control-Allow-Origin", "*");
        res.add_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
        res.add_header("Access-Control-Allow-Headers", "Content-Type, Authorization");
        res.add_header("Access-Control-Max-Age", "86400");
        return res;
    });

    
    int rc=sqlite3_open(DATABASE_PATH.c_str(),&db);
    if(rc){
        std::cerr<<"failed to open db";
        goto RET;
    }

    CROW_ROUTE(app, "/").methods("GET"_method)([](crow::request& req, crow::response& res) {
        res.redirect("/static/swagger/index.html");
        res.end();
    });

    CROW_ROUTE(app,"/getUsers").methods("GET"_method)([](crow::request& req, crow::response& res){
        auto data=get_users_from_db();
        res.set_header("Content-Type", "application/json");
        res.add_header("Access-Control-Allow-Origin", "*");
        res.body=data.dump(); 
        res.end();
    });
    
    CROW_ROUTE(app, "/random").methods("GET"_method)([](crow::request& req, crow::response& res){
        res.add_header("Access-Control-Allow-Origin", "*");
        res.body=get_random_number();
        res.end();
    });
    
    app.port(1337).multithreaded().run();
    
    END_PROCESSES:
    sqlite3_finalize(stmt);
    sqlite3_close(db);
    
    RET:
    return STATUS_CODE;
}