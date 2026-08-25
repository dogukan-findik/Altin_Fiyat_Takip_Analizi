using System.Net.Http.Headers;
using System.Net.Http.Json;

namespace Altin_Fiyat_Takip_Analizi.Web.Services;

public class ApiService
{
    private readonly HttpClient _http;
    private string? _token;

    public event Action? AuthStateChanged;

    public string? CurrentUsername { get; private set; }
    public string? CurrentRole { get; private set; }

    public void SetCurrentUser(string username, string role)
    {
        CurrentUsername = username;
        CurrentRole = role;
        AuthStateChanged?.Invoke();
    }
    

    public ApiService(HttpClient http)
    {
        _http = http;
    }

    public bool IsAuthenticated => _token is not null;

    public void SetToken(string token)
    {
        _token = token;
        _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
        AuthStateChanged?.Invoke();
    }

    public void ClearToken()
    {
        _token = null;
        _http.DefaultRequestHeaders.Authorization = null;
        CurrentUsername = null;
        CurrentRole = null;
        AuthStateChanged?.Invoke();
    }

    public async Task<T?> GetAsync<T>(string endpoint)
    {
        var response = await _http.GetAsync(endpoint);
        if (!response.IsSuccessStatusCode) return default;
        return await response.Content.ReadFromJsonAsync<T>();
    }

    public async Task<TResponse?> PostAsync<TRequest, TResponse>(string endpoint, TRequest body)
    {
        var response = await _http.PostAsJsonAsync(endpoint, body);
        if (!response.IsSuccessStatusCode) return default;
        return await response.Content.ReadFromJsonAsync<TResponse>();
    }

    public async Task<bool> PutAsync<TRequest>(string endpoint, TRequest body)
    {
        var response = await _http.PutAsJsonAsync(endpoint, body);
        return response.IsSuccessStatusCode;
    }

    public async Task<bool> DeleteAsync(string endpoint)
    {
        var response = await _http.DeleteAsync(endpoint);
        return response.IsSuccessStatusCode;
    }

    public async Task<TResponse?> PostEmptyAsync<TResponse>(string endpoint)
    {
        var response = await _http.PostAsync(endpoint, null);
        if (!response.IsSuccessStatusCode) return default;
        return await response.Content.ReadFromJsonAsync<TResponse>();
    }
}