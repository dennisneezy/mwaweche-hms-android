package com.mwaeche.hms

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme { ServerConnectScreen() } }
    }
}

@Composable
private fun ServerConnectScreen() {
    var address by remember { mutableStateOf("https://") }
    var status by remember { mutableStateOf("Enter the mother server address to connect.") }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Text("Mwaeche HMS", style = MaterialTheme.typography.headlineMedium)
        Text("Connect to your hospital server", style = MaterialTheme.typography.titleMedium)
        OutlinedTextField(value = address, onValueChange = { address = it }, label = { Text("Server URL") }, placeholder = { Text("https://hms-server.hospital.local") }, singleLine = true, modifier = Modifier.fillMaxWidth())
        Button(enabled = !busy && address.startsWith("https://"), onClick = {
            busy = true; status = "Checking server…"
            scope.launch {
                status = withContext(Dispatchers.IO) {
                    try {
                        val clean = address.trim().trimEnd('/')
                        val conn = (URL("$clean/api/health").openConnection() as HttpURLConnection)
                        conn.requestMethod = "GET"; conn.connectTimeout = 4000; conn.readTimeout = 4000
                        val code = conn.responseCode
                        conn.disconnect()
                        if (code == 200) "Server responded. Server identity verification and login are the next setup step." else "Server responded with HTTP $code. Check the server configuration."
                    } catch (_: Exception) { "Could not connect. Check Wi-Fi, server address, firewall and HTTPS certificate." }
                }
                busy = false
            }
        }, modifier = Modifier.fillMaxWidth()) { Text(if (busy) "Checking…" else "Test connection") }
        Text(status, style = MaterialTheme.typography.bodyMedium)
        HorizontalDivider()
        Text("Offline mode", style = MaterialTheme.typography.titleMedium)
        Text("This starter does not yet allow clinical or financial edits offline. The planned sync queue will use idempotency keys and version checks so conflicts are reviewed rather than silently overwriting server records.")
        Text("Security: use HTTPS. This app intentionally refuses to test plain HTTP addresses.", style = MaterialTheme.typography.bodySmall)
    }
}
