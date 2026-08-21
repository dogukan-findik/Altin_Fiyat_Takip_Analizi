using Altin_Fiyat_Takip_Analizi.Web.Components;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddHttpClient("AltinFiyatApiClient", client =>
{
    client.BaseAddress = new Uri("https://localhost:7268/");
});

builder.Services.AddScoped<Altin_Fiyat_Takip_Analizi.Web.Services.ApiService>(sp =>
{
    var factory = sp.GetRequiredService<IHttpClientFactory>();
    var httpClient = factory.CreateClient("AltinFiyatApiClient");
    return new Altin_Fiyat_Takip_Analizi.Web.Services.ApiService(httpClient);
});

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();

app.UseStaticFiles();
app.UseAntiforgery();

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
