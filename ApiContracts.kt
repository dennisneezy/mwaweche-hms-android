package com.mwaeche.hms.data

import retrofit2.http.*

data class HealthResponse(val application: String, val server_id: String, val server_name: String, val status: String)
data class LoginRequest(val username: String, val password: String)
data class LoginResponse(val access_token: String, val token_type: String, val expires_in: Int, val role: String)
data class PatientSummary(val patient_id: String, val full_name: String, val patient_type: String?, val version: Long)
data class SyncMutation(val mutation_id: String, val entity_type: String, val entity_id: String, val operation: String, val payload: Map<String, String>, val base_version: Long)
data class SyncResult(val mutation_id: String, val status: String, val server_version: Long? = null, val message: String? = null)

interface MwaecheApi {
    @GET("api/health") suspend fun health(): HealthResponse
    @POST("api/auth/login") suspend fun login(@Body request: LoginRequest): LoginResponse
    @GET("api/patients") suspend fun patients(@Query("q") query: String): List<PatientSummary>
    @POST("api/sync/mutations") suspend fun sync(@Body mutation: SyncMutation): SyncResult
}
