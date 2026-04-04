const crypto = require("crypto");
const http = require("http");
const fs = require("fs");
const [keyId, secret] = "69cdd2c882a89443a06c4758:acd2dd504ed3e680d3a9d0514479e75a7b82a3a27d7549ab0695ae6753b3d6bc".split(":");

function makeToken() {
    const h = Buffer.from(JSON.stringify({alg:"HS256",typ:"JWT",kid:keyId})).toString("base64url");
    const n = Math.floor(Date.now()/1000);
    const p = Buffer.from(JSON.stringify({iat:n,exp:n+300,aud:"/admin/"})).toString("base64url");
    const m = crypto.createHmac("sha256", Buffer.from(secret,"hex"));
    m.update(h+"."+p);
    return h+"."+p+"."+m.digest("base64url");
}

function apiCall(method, path, body) {
    return new Promise((resolve) => {
        const opts = {hostname:"localhost",port:2368,path,method,
            headers:{"Authorization":"Ghost "+makeToken(),"Content-Type":"application/json"}};
        if (body) opts.headers["Content-Length"] = Buffer.byteLength(body);
        const req = http.request(opts, res => {
            let d=""; res.on("data",c=>d+=c);
            res.on("end",()=>resolve({status:res.statusCode,data:d}));
        });
        if (body) req.write(body);
        req.end();
    });
}

const dates = {
    "stlouis-to-caruthersville": "2014-06-01T12:00:00.000Z",
    "caruthersville-to-memphis": "2013-06-01T12:00:00.000Z",
    "memphis-to-helena": "2013-06-01T12:00:00.000Z",
    "helena-to-greenville": "2013-06-01T12:00:00.000Z",
    "greenville-to-vicksburg": "2013-06-01T12:00:00.000Z",
    "vicksburg-to-baton-rouge": "2014-06-01T12:00:00.000Z",
    "atchafalaya-river": "2015-06-01T12:00:00.000Z",
    "baton-rouge-to-venice": "2015-06-01T12:00:00.000Z",
    "birdsfoot-delta": "2015-06-01T12:00:00.000Z",
};

async function main() {
    // Delete existing posts
    let res = await apiCall("GET","/ghost/api/admin/posts/?limit=all&fields=id");
    let existing = JSON.parse(res.data).posts || [];
    console.log("Deleting",existing.length,"posts...");
    for (const p of existing) await apiCall("DELETE","/ghost/api/admin/posts/"+p.id+"/");

    // Delete existing pages
    res = await apiCall("GET","/ghost/api/admin/pages/?limit=all&fields=id");
    let pages = JSON.parse(res.data).pages || [];
    console.log("Deleting",pages.length,"pages...");
    for (const p of pages) await apiCall("DELETE","/ghost/api/admin/pages/"+p.id+"/");

    // Create new posts
    const posts = JSON.parse(fs.readFileSync("/tmp/ghost-import-v4.json","utf8"));
    console.log("Creating",posts.length,"posts...");
    let ok=0, fail=0;
    for (const post of posts) {
        const tags = [{name:post.section_name, slug:post.section}];
        if (post.post_type==="mile-marker") tags.push({name:"#mile-marker",slug:"hash-mile-marker"});
        tags.push({name:"#river-log",slug:"hash-river-log"});

        const pubDate = dates[post.section] || "2013-06-01T12:00:00.000Z";

        const r = await apiCall("POST","/ghost/api/admin/posts/?source=html",
            JSON.stringify({posts:[{
                title:post.title, slug:post.slug, html:post.html,
                status:"published", tags, custom_excerpt:post.excerpt||"",
                published_at:pubDate, created_at:pubDate
            }]}));
        if (r.status===201) { ok++; if(ok%100===0) console.log("  Created",ok); }
        else { fail++; if(fail<=3) console.log("  FAIL:",post.title.substring(0,50),r.status); }
    }
    console.log("Done!",ok,"created,",fail,"failed");
}
main();
